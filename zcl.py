#!zcl.py

class Cluster():
    Basic = "0000"
    PowerConfig = "0001"
    Identify = "0003"
    OnOff = "0006"
    LevelCtrl = "0008"
    OTA = "0019"
    PollCtrl = "0020"
    ColourCtrl = "0300"
    Illuminance = "0400"
    Temperature = "0402"
    Occupancy = "0406"
    IAS_Zone = "0500"
    SimpleMetering = "0702"

class Attribute():
    Manuf_Name = "0004" # Basic cluster, string (Read Only)
    Model_Name = "0005" # Basic cluster, string (Read Only)
    Batt_Voltage = "0020" # Power_Config cluster, 8 bit in 0.1V steps (Read Only)
    Batt_Percentage = "0021" # Power_Config cluster, 8-bit in 0.5% steps (Read Only)
    OnOffState = "0000" # OnOff cluster, 8 bit bool
    firmwareVersion = "0002" # OTA version number
    Hue = "0000" # For ColorCtrl (Read Only)
    Saturation = "0001"# For ColorCtrl (Read Only)
    Log_Lux = "0000" # Illuminance cluster, 16-bit as 10000 x log(10)Lux + 1 (Read Only)
    Celsius = "0000" # Temperature cluster, 16-bit in 0.01'C steps (Read Only)
    Zone_Type = "0001" # IAS Zone cluster, enum list - see below (Read Only)
    CurrentSummationDelivered = "0000" # Simple Metering cluster. value in Wh (Read Only)
    InstantaneousDemand =  "0400"  # Simple Metering cluster. value in W (Read Only)

class AttributeTypes():
    Boolean = "10"
    BitMap8 = "18"
    Uint8 = "20"
    Uint16 = "21"
    Uint32 = "23"
    Uint48 = "25"   # For CurrentSummation
    Sint8 = "28"
    Sint16 = "29"
    Sint24 = "2A"   # For InstantaneousDemand
    Sint32 = "2B"
    Sint48 = "2D"
    Enum8 = "30"
    Enum16 = "31"
    OctStr = "41"
    ChrStr = "42"
    LChrStr = "43"

class Zone_Type():
    PIR = "000D"
    Contact = "0015"

# Zone_Status_bits 0 is Alarm1, bit 1 is Alarm2, bit 2 is Tamper and bit 3 is LowBattery
