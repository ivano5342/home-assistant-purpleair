import asyncio
from datetime import timedelta
import logging

import math

import aiohttp

from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval, async_track_point_in_utc_time
from homeassistant.util import dt

from .const import AQI_BREAKPOINTS, DISPATCHER_PURPLE_AIR, PARTICLE_PROPS, LOCAL_SCAN_INTERVAL, LOCAL_URL_FORMAT, \
    TEMP_ADJUSTMENT, HUMIDITY_ADJUSTMENT

_LOGGER = logging.getLogger(__name__)


def calc_aqi(value, index):
    if index not in AQI_BREAKPOINTS:
        _LOGGER.debug('calc_aqi requested for unknown type: %s', index)
        return None

    bp = next((bp for bp in AQI_BREAKPOINTS[index] if bp['pm_low'] <= value <= bp['pm_high']), None)
    if not bp:
        _LOGGER.debug('value %s did not fall in valid range for type %s', value, index)
        return None

    aqi_range = bp['aqi_high'] - bp['aqi_low']
    pm_range = bp['pm_high'] - bp['pm_low']
    c = value - bp['pm_low']
    return round((aqi_range/pm_range) * c + bp['aqi_low'])


# LRAPA conversion using the same formula as used by PurpleAir's map as of 2020-09-06
def lrapa(value):
    return max(0, 0.5 * value - 0.66)


def calc_dewpoint(temp_f, humidity):
    """
    Calculate dewpoint using August-Roche-Magnus approximation.
    Note: Rounding twice for both F>C and C>F conversions simply because the purpleair website does this (so I
    do this too, to match the purpleair website).
    """
    if humidity <= 0:
        return 0

    temp_c = round((temp_f - 32) * 5.0/9.0)

    numerator = 243.04 * (math.log(humidity / 100) + ((17.625 * temp_c) / (243.04 + temp_c)))
    denominator = 17.625 - math.log(humidity / 100) - ((17.625 * temp_c) / (243.04 + temp_c))
    dew_point_c = numerator / denominator

    dew_point_f = round((dew_point_c * 9/5) + 32)
    return dew_point_f


def process_heat_adjustments(json_result):
    """Since the purple air devices are affected by heat from itself, modify readings to account for difference"""
    current_temp = float(json_result.get('current_temp_f', 0))
    current_humidity = float(json_result.get('current_humidity', 0))
    new_temp = current_temp + TEMP_ADJUSTMENT
    new_humid = max(0, min(100, current_humidity + HUMIDITY_ADJUSTMENT))

    return {
        'current_temp': new_temp,
        'current_humidity': new_humid,
        'current_dewpoint': calc_dewpoint(new_temp, new_humid)
    }


def process_pm_readings(json_result, is_dual = False):
    """Processes Particle mass readings and confidence of said readings"""
    readings = {'pm2_5_aqi_raw': json_result.get('pm2.5_aqi')}
    if is_dual:
        readings['pm2_5_aqi_b_raw'] = json_result.get('pm2.5_aqi_b')

    for prop in PARTICLE_PROPS:
        if prop not in json_result:
            readings[prop] = None
            continue

        a = float(json_result[prop])
        prop_b = prop + '_b'  # Property name for sensor B
        if is_dual and json_result.get(prop_b) is not None:
            (value, confidence) = process_dual_sensor_readings(a, float(json_result[prop_b]))
        else:
            value = a
            confidence = 'Good'

        readings[prop] = value
        readings[f'{prop}_conf'] = confidence

    readings['aqi_epa'] = calc_aqi(readings['pm2_5_atm'], 'pm2_5')
    readings['aqi_lrapa'] = calc_aqi(lrapa(readings['pm2_5_atm']), 'pm2_5')
    #
    readings['aqi_tvoc'] = json_result.get('gas_680')
    readings['pm1_0_atm'] = json_result.get('pm1_0_atm')
    readings['pm2_5_atm'] = json_result.get('pm2_5_atm')
    readings['pm10_0_atm'] = json_result.get('pm10_0_atm')
    readings['pm1_0_atm_b'] = json_result.get('pm1_0_atm_b')
    readings['pm2_5_atm_b'] = json_result.get('pm2_5_atm_b')
    readings['pm10_0_atm_b'] = json_result.get('pm10_0_atm_b')
    readings['p_0_3_um'] = json_result.get('p_0_3_um')
    readings['p_0_5_um'] = json_result.get('p_0_5_um')
    readings['p_1_0_um'] = json_result.get('p_1_0_um')
    readings['p_2_5_um'] = json_result.get('p_2_5_um')
    readings['p_5_0_um'] = json_result.get('p_5_0_um')
    readings['p_10_0_um'] = json_result.get('p_10_0_um_b')
    readings['p_0_3_um_b'] = json_result.get('p_0_3_um_b')
    readings['p_0_5_um_b'] = json_result.get('p_0_5_um_b')
    readings['p_1_0_um_b'] = json_result.get('p_1_0_um_b')
    readings['p_2_5_um_b'] = json_result.get('p_2_5_um_b')
    readings['p_5_0_um_b'] = json_result.get('p_5_0_um_b')
    readings['p_10_0_um_b'] = json_result.get('p_10_0_um_b')
    readings['p25aqic'] = json_result.get('p25aqic')
    readings['p25aqic_b'] = json_result.get('p25aqic_b')
    #
    return readings

def process_dual_sensor_readings(a, b):
    value = round((a + b) / 2, 1)

    if abs(a - b) < 45:
        confidence = 'Good'
    elif abs(a - b) > 300:
        # If the readings are so severly different, one is probably affected by a
        # physical obstuction (spider?), so just throw it away and use the smaller value.
        confidence = 'Severe'
        value = min(a, b)
    else:
        confidence = 'Questionable'

    return (value, confidence)


class PurpleAirApi:
    def __init__(self, hass, session):
        self._hass = hass
        self._session = session
        self._nodes = {}
        self._data = {}
        self._last_success = {}
        self._failed_polls = {}
        self._scan_interval = timedelta(seconds=LOCAL_SCAN_INTERVAL)
        self._grace_period = timedelta(seconds=90)
        self._shutdown_interval = None
        self._update_lock = asyncio.Lock()

    def is_node_registered(self, pa_sensor_id):
        return pa_sensor_id in self._data

    def get_reading(self, pa_sensor_id, prop):
        if pa_sensor_id not in self._data:
            return None

        node = self._data[pa_sensor_id]
        return node[prop] if prop in node else None

    def register_node(self, pa_sensor_id, ip_address):
        if pa_sensor_id in self._nodes:
            _LOGGER.debug('detected duplicate registration: %s', pa_sensor_id)
            return

        self._nodes[pa_sensor_id] = { 'ip_address': ip_address }
        _LOGGER.debug('registered new node: %s', pa_sensor_id)

        if not self._shutdown_interval:
            _LOGGER.debug('starting background poll: %s', self._scan_interval)
            self._shutdown_interval = async_track_time_interval(
                self._hass,
                self._update,
                self._scan_interval
            )

            async_track_point_in_utc_time(
                self._hass,
                self._update,
                dt.utcnow() + timedelta(seconds=5)
            )

    def unregister_node(self, pa_sensor_id):
        if pa_sensor_id not in self._nodes:
            _LOGGER.debug('detected non-existent unregistration: %s', pa_sensor_id)
            return

        del self._nodes[pa_sensor_id]
        _LOGGER.debug('unregistered node: %s', pa_sensor_id)

        if not self._nodes and self._shutdown_interval:
            _LOGGER.debug('no more nodes, shutting down interval')
            self._shutdown_interval()
            self._shutdown_interval = None


    async def _fetch_data(self, local_node_ips):
        if not local_node_ips:
            _LOGGER.debug('no nodes provided')
            return {}

        urls = list(map(LOCAL_URL_FORMAT.format, local_node_ips))
        _LOGGER.debug('fetch url list: %s', urls)

        results = {}
        for ip_address in local_node_ips:
            url = LOCAL_URL_FORMAT.format(ip_address)
            _LOGGER.debug('fetching url: %s', url)

            try:
                timeout = aiohttp.ClientTimeout(total=8)
                async with self._session.get(url, timeout=timeout) as response:
                    if response.status != 200:
                        _LOGGER.warning('bad API response for %s: %s', url, response.status)
                        continue

                    json = await response.json()
                    results[ip_address] = json
            except asyncio.TimeoutError as err:
                _LOGGER.warning('Timed out fetching Purple Air device %s: %s', ip_address, err)
            except Exception as err:
                _LOGGER.error('Unable to connect to Purple Air device %s: %s', ip_address, err)

        return results

    async def _update(self, now=None):
        local_node_ips = [n['ip_address'] for n in self._nodes.values()]
        _LOGGER.debug('Purple Air nodes: %s', local_node_ips)

        if self._update_lock.locked():
            _LOGGER.debug('Skipping poll tick because previous update is still running')
            return

        async with self._update_lock:
            results = await self._fetch_data(local_node_ips)
            nodes = dict(self._data)
            poll_time = dt.utcnow()

            for registered_sensor_id, node in self._nodes.items():
                ip_address = node['ip_address']
                result = results.get(ip_address)

                if result is None:
                    previous_failures = self._failed_polls.get(registered_sensor_id, 0) + 1
                    self._failed_polls[registered_sensor_id] = previous_failures
                    last_success = self._last_success.get(registered_sensor_id)
                    if last_success is not None and poll_time - last_success >= self._grace_period:
                        nodes.pop(registered_sensor_id, None)
                        self._last_success.pop(registered_sensor_id, None)
                        self._failed_polls.pop(registered_sensor_id, None)
                        _LOGGER.debug('Dropped stale sensor %s after %s seconds without a good reply', registered_sensor_id, (poll_time - last_success).total_seconds())
                    continue

                try:
                    pa_sensor_id = result['SensorId']
                    is_dual = 'pm2.5_aqi_b' in result
                    new_node = {
                        'device_location': result['place'],
                        'rssi': result['rssi'],
                        'current_temp_raw': float(result['current_temp_f']),
                        'current_humidity_raw': float(result['current_humidity']),
                        'current_dewpoint_raw': float(result.get('current_dewpoint_f', 0)),
                        'pressure': float(result.get('pressure', 0)),
                        'is_dual': is_dual
                    }
                    new_node.update(process_pm_readings(result, is_dual))
                    new_node.update(process_heat_adjustments(result))
                    nodes[pa_sensor_id] = new_node
                    previous_failures = self._failed_polls.get(pa_sensor_id, 0)
                    if previous_failures:
                        _LOGGER.info('Recovered sensor %s after %s failed polls', pa_sensor_id, previous_failures)
                    self._failed_polls[pa_sensor_id] = 0
                    self._last_success[pa_sensor_id] = poll_time
                    _LOGGER.debug('Json results for %s: %s', pa_sensor_id, result)
                    _LOGGER.debug('Readings for %s: %s', pa_sensor_id, nodes[pa_sensor_id])
                except (KeyError, TypeError, ValueError) as err:
                    self._failed_polls[registered_sensor_id] = self._failed_polls.get(registered_sensor_id, 0) + 1
                    _LOGGER.error('Unable to parse Purple Air data for %s: %s', registered_sensor_id, err)

            self._data = nodes
            async_dispatcher_send(self._hass, DISPATCHER_PURPLE_AIR)
