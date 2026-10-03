"""Constants for the Purple Air integration."""
#from homeassistant.const import TEMP_FAHRENHEIT, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, PRESSURE_HPA,PERCENTAGE, DEVICE_CLASS_AQI #old
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfPressure,
    UnitOfTemperature,
)

AQI_BREAKPOINTS = {
    'pm2_5': [
        { 'pm_low': 500.5, 'pm_high': 999.9, 'aqi_low': 501, 'aqi_high': 999 },
        { 'pm_low': 350.5, 'pm_high': 500.4, 'aqi_low': 401, 'aqi_high': 500 },
        { 'pm_low': 250.5, 'pm_high': 350.4, 'aqi_low': 301, 'aqi_high': 400 },
        { 'pm_low': 150.5, 'pm_high': 250.4, 'aqi_low': 201, 'aqi_high': 300 },
        { 'pm_low':  55.5, 'pm_high': 150.4, 'aqi_low': 151, 'aqi_high': 200 },
        { 'pm_low':  35.5, 'pm_high':  55.4, 'aqi_low': 101, 'aqi_high': 150 },
        { 'pm_low':  12.1, 'pm_high':  35.4, 'aqi_low':  51, 'aqi_high': 100 },
        { 'pm_low':     0, 'pm_high':  12.0, 'aqi_low':   0, 'aqi_high':  50 },
    ],
}
PARTICLE_PROPS = ['pm1_0_atm', 'pm2_5_atm', 'pm10_0_atm']

# Map of sensors to create entities for
# todo: fix these device classes and use the current ones 'SensorDeviceClass'
#    'pm2_5_a_raw':             {'key': 'pm2_5_a_raw',      'uom': DEVICE_CLASS_AQI, 'icon': 'mdi:blur-linear'},
#    'pm2_5_b_raw':             {'key': 'pm2_5_b_raw',      'uom': DEVICE_CLASS_AQI, 'icon': 'mdi:blur-linear'},
# https://github.com/home-assistant/developers.home-assistant/blob/master/docs/core/entity/sensor.md
SENSORS_MAP = {
    'pm2_5_aqi_a_raw':         {'key': 'pm2_5_aqi_raw',    'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur-linear'},
    'pm2_5_aqi_b_raw':         {'key': 'pm2_5_aqi_b_raw',  'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur-linear'},
    'pm2_5_atm_confidence':    {'key': 'pm2_5_atm_conf',   'uom': None,             'icon': 'mdi:seal'},
    'pm2_5_aqi_rgb_a':         {'key': 'p25aqic',          'uom': None,             'icon': 'mdi:seal'},
    'pm2_5_aqi_rgb_b':         {'key': 'p25aqic_b',        'uom': None,             'icon': 'mdi:seal'},
    'particulate_matter_0_1':  {'key': 'pm1_0_atm',        'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'particulate_matter_2_5':  {'key': 'pm2_5_atm',        'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'particulate_matter_10':   {'key': 'pm10_0_atm',       'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'air_quality_index_epa':   {'key': 'aqi_epa',          'uom': SensorDeviceClass.AQI, 'icon': 'mdi:weather-hazy'},
    'air_quality_index_lrapa': {'key': 'aqi_lrapa',        'uom': SensorDeviceClass.AQI, 'icon': 'mdi:weather-hazy'},
    'pm1_0_atm':               {'key': 'pm1_0_atm',        'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'pm2_5_atm':               {'key': 'pm2_5_atm',        'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'pm10_0_atm':              {'key': 'pm10_0_atm',       'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'pm1_0_atm_b':             {'key': 'pm1_0_atm_b',      'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'pm2_5_atm_b':             {'key': 'pm2_5_atm_b',      'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'pm10_0_atm_b':            {'key': 'pm10_0_atm_b',     'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_0_3_um':                {'key': 'p_0_3_um',         'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_0_5_um':                {'key': 'p_0_5_um',         'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_1_0_um':                {'key': 'p_1_0_um',         'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_2_5_um':                {'key': 'p_2_5_um',         'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_5_0_um':                {'key': 'p_5_0_um',         'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_10_0_um':               {'key': 'p_10_0_um',        'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_0_3_um_b':              {'key': 'p_0_3_um_b',       'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_0_5_um_b':              {'key': 'p_0_5_um_b',       'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_1_0_um_b':              {'key': 'p_1_0_um_b',       'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_2_5_um_b':              {'key': 'p_2_5_um_b',       'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_5_0_um_b':              {'key': 'p_5_0_um_b',       'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'p_10_0_um_b':             {'key': 'p_10_0_um_b',      'uom': SensorDeviceClass.AQI, 'icon': 'mdi:blur'},
    'vocs':                    {'key': 'aqi_tvoc',         'uom': SensorDeviceClass.AQI, 'icon': "mdi:blur"},
    'humidity':                {'key': 'current_humidity', 'uom': PERCENTAGE,       'icon': 'mdi:water-percent'},
    'temperature':             {'key': 'current_temp',     'uom': UnitOfTemperature.FAHRENHEIT,  'icon': 'mdi:thermometer'},
    'dewpoint':                {'key': 'current_dewpoint', 'uom': UnitOfTemperature.FAHRENHEIT,  'icon': 'mdi:water-outline'},
    'pressure':                {'key': 'pressure',         'uom': UnitOfPressure.HPA,     'icon': 'mdi:gauge'},
    'rssi':                    {'key': 'rssi',             'uom': SIGNAL_STRENGTH_DECIBELS_MILLIWATT, 'icon': 'mdi:wifi'}
}
SENSORS_DUAL_ONLY = ['pm2_5_aqi_b_raw']

MANUFACTURER = "Purple Air"
DISPATCHER_PURPLE_AIR = "dispatcher_purple_air"
DOMAIN = "purpleair"
TEMP_ADJUSTMENT = -8  # From PurpleAir javascript: `(parseInt(temp) + -8).toFixed(0);`
HUMIDITY_ADJUSTMENT = (
    +4  
) # From PurpleAir javascript: `(hum = parseInt(hum) + 4) > 100 && (hum = 100)`

LOCAL_SCAN_INTERVAL = 10
LOCAL_URL_FORMAT = "http://{0}/json?live=true"

# Models
PMS_SENSOR = "PMS"
BME_SENSOR = "BME"
MODEL_PA_1 = "PA-I"
MODEL_PA_2 = "PA-II"
MODEL_PA_FLEX = "PA-II-FLEX"
