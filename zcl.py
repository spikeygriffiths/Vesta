#!zcl.py

class Cluster():
    Basic = "0000"
    PowerConfig = "0001"
    Identify = "0003"
    OnOff = "0006"
    LevelCtrl = "0008"
    Time = "000A"
    OTA = "0019"
    PollCtrl = "0020"
    ColourCtrl = "0300"
    Thermostat = "0201"
    Illuminance = "0400"
    Temperature = "0402"
    Occupancy = "0406"
    IAS_Zone = "0500"
    SimpleMetering = "0702"

class Attribute():
    # Basic
    Manuf_Name = "0004" # RO Basic cluster, string
    Model_Name = "0005" # RO Basic cluster, string
    # PowerConfig
    Batt_Voltage = "0020" # RO U8 Power_Config cluster, 0.1V steps
    Batt_Percentage = "0021" # R0 U8 Power_Config cluster, 0.5% steps
    # OnOff
    OnOffState = "0000" # RO U8 OnOff cluster
    # Time
    Time = "0000" # WR UTC as U32 in seconds since midnight 1/1/2000
    TimeStatus = "0001" # WR 8-Bitmap. 
    TimeZone = "0002" # RW S32
    DstStart ="0003" #  RW U32 this year's Summer Time start, U32 as for Time
    DstEnd = "0004" # RW U32 As above, but end
    DstShift = "0005" # RW S32 in seconds (-86400 -> +86400)
    StandardTime = "0006"   # RO U32 Time+TimeZone (but not DST)
    LocalTime = "0007" # RO U32 Time+TimeZone+DST
    LastSetTime = "0008" # RO UTC
    ValidUntilTime = "0009" # RW UTC
    # OTA
    firmwareVersion = "0002" # RO U32 version number, stack in bottom 16, app in top 16.  4 bits each for major.minor.release.build
    # PollCtrl
    CheckInIntervalQs = "0000"  # RW U32
    LongPollIntervalQs = "0001" # RO U32
    ShortPollIntervalQs = "0002" # RO U16
    FastPollTimeoutQs = "0003" # RW U16
    CheckInIntervalMinQs = "0004" # RO U32
    LongPollIntervalMinQs = "0005" # RO U32
    FastPollTimeoutMaxQs = "0006" # RO U16
    # ColorCtrl
    Hue = "0000" # For ColorCtrl (Read Only)
    Saturation = "0001" # For ColorCtrl (Read Only)
    # Thermostat
    LocalTemp = "0000" # RO S16 Source temp in 0.01'C
    OccupiedHeatingSetPoint = "0012" # RW S16 Target temp in 0.01'C
    #ThermostatProgrammingOperationMode = "0025" # RW 8-bit bitmap
    #OccupiedHeatingSetPoint = "0014" # Unoccupied Heating RW S16 Target temp in 0.01'C
    StartOfWeek = "0020" # RO ENUM8, 0=Sun, etc.
    # Illuminance
    Log_Lux = "0000" # Illuminance cluster, 16-bit as 10000 x log(10)Lux + 1 (Read Only)
    # Temperature
    Celsius = "0000" # Temperature cluster, 16-bit in 0.01'C steps (Read Only)
    # IAS_Zone
    Zone_Type = "0001" # IAS Zone cluster, enum list - see below (Read Only)
    # Simple Metering cluster
    CurrentSummationDelivered = "0000" # Value in Wh (Read Only, unsigned 48-bit int).  Energy consumed
    CurrentSummationReceived = "0001" # Value in Wh (Read Only, unsigned 48-bit int).  Energy generated
    DefaultUpdatePeriod = "000A"    # Standard sampling period in seconds, probably 30s (Read Only, 8-bit)
    FastPollUpdatePeriod = "000B"   # Fast sampling period in seconds, probably 5s (Read Only, 8-bit), for use with RequestFastPollMode command
    UnitOfMeasure = "0300" # 8-bit enumeration, 0x00=kW/kWh, 1=m3/m3h
    Multiplier = "0301" # Uint24
    Divisor = "0302" # Uint24
    InstantaneousDemand =  "0400"  # Value in W (Read Only, signed 24-bit int). +ve is consumed, -ve is generated

class Commands():
    ReadAttributes = "00" # General commands
    ReadAttrRsp = "01"
    WriteAttributes = "02"
    WriteAttrRsp = "04"
    ReportAttr = "0A"
    AdjustSetpoint = "00" # Thermostat Client->server
    GetScheduleRsp = "00" # Server->client
    SetSchedule = "01"
    GetSchedule = "02"
    ClrSchedule = "03"

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
    UtcTime = "E2"  # Seconds since midnight, 1/1/2000

class Zone_Type():
    PIR = "000D"
    Contact = "0015"

# Zone_Status_bits 0 is Alarm1, bit 1 is Alarm2, bit 2 is Tamper and bit 3 is LowBattery
