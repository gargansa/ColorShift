
from ..Script import Script
import random
import re


# Convenience function for gargansa's coding familiarity
def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


# Function to compile extruder info into a string
def adjust_extruder_rate(existing_gcode, *ext):
    i = 0
    for item in ext:
        if i == 0:
            setup_line = existing_gcode + "\nM567 P0 E" + str(item)
        else:
            setup_line += ":" + str(item)
        i += 1
    setup_line += "\n"
    return setup_line


# Just used to output info to text file to help debug
def print_debug(*report_data):
    setup_line = ";Debug "
    for item in report_data:
        setup_line += str(item)
    setup_line += "\n"
    return setup_line


class Melt(Script):
    version = "4.0.0"

    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"Multi-Extruder Layering Tool """ + self.version + """ (MELT)",
            "key":"Melt",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "firmware_type":
                {
                    "label": "Firmware Type",
                    "description": "Type of Firmware Supported.",
                    "type": "enum",
                    "options": {"duet":"Duet"},
                    "default_value": "duet"
                },
                "qty_extruders":
                {
                    "label": "Number of extruders",
                    "description": "How many total extruders in mixing nozzle.",
                    "type": "enum",
                    "options": {"2":"Two","3":"Three","4":"Four"},
                    "default_value": "2"
                },
                "affected_tool":
                {
                    "label": "Tool Affected",
                    "description": "Which Tool(Part) to Apply Color or Effect.",
                    "type": "enum",
                    "options": {"0":"All","1":"Tool 1","2":"Tool 2","3":"Tool 3","4":"Tool 4","5":"Tool 5","6":"Tool 6","7":"Tool 7","8":"Tool 8","9":"Tool 9","10":"Tool 10","11":"Tool 11","12":"Tool 12","13":"Tool 13","14":"Tool 14","15":"Tool 15"},
                    "default_value": "0"
                },
                "effect_type":
                {
                    "label": "Blend or Effect",
                    "description": "Choose whether to apply a stationary blend to the tool or a changing effect such as a gradient",
                    "type": "enum",
                    "options": {"blend":"Define Blend","effect":"Changing Effect"},
                    "default_value": "blend"
                },
                "unit_type":
                {
                    "label": "Unit Type",
                    "description": "Percentage or Layer Unit.",
                    "type": "enum",
                    "options": {"percent":"Percentage","layer_no":"Layer No."},
                    "default_value": "percent"
                },
                "percent_change_start":
                {
                    "label": "Location % Start",
                    "description": "Percentage location of layer height to begin effect.",
                    "unit": "%",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "minimum_value_warning": "0",
                    "maximum_value_warning": "99",
                    "enabled": "a_trigger == 'percent'"
                },
                "percent_change_end":
                {
                    "label": "Location % End",
                    "description": "Percentage location of layer height to end effect.",
                    "unit": "%",
                    "type": "float",
                    "default_value": 100,
                    "minimum_value": "0",
                    "maximum_value": "100",
                    "minimum_value_warning": "1",
                    "maximum_value_warning": "100",
                    "enabled": "a_trigger == 'percent' and effect_type == 'effect'"
                },
                "layer_change_start":
                {
                    "label": "Location # Start",
                    "description": "Layer location to begin effect.",
                    "unit": "#",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": "0",
                    "enabled": "a_trigger == 'layer_no'"
                },
                "layer_change_end":
                {
                    "label": "Location # End",
                    "description": "Layer location to end effect.",
                    "unit": "#",
                    "type": "int",
                    "default_value": 100000,
                    "minimum_value": "0",
                    "enabled": "a_trigger == 'layer_no' and effect_type == 'effect'"
                },
                "blend_values":
                {
                    "label": "Values",
                    "description": "What percentage values to set the extruder blend. Must add up to 100%",
                    "type": "str",
                    "default_value": "100,0,0,0",
                    "enabled": "effect_type == 'blend'"
                },
                "rotation_order":
                {
                    "label": "Extruder Rotation",
                    "description": "The order in which the shift moves through the extruders. Example 'ca' starts the shift at extruder c and moves towards extruder a. If only shifting through two layers list only those two. Must be lowercase. Must be at least two letters or it will default to ab",
                    "type": "str",
                    "default_value": "abcd",
                    "enabled": "effect_type == 'effect'"
                },
                "extruder_a_start":
                {
                    "label": "Extruder A begin clamp",
                    "description": "The beginning percentage to start extruder a.",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "'a' or in rotation_order and effect_type == 'effect'"
                },
                "extruder_a_end":
                {
                    "label": "Extruder A end clamp",
                    "description": "The ending percentage to start extruder a.",
                    "type": "float",
                    "default_value": 100,
                    "enabled": "'a' in rotation_order and effect_type == 'effect'"
                },
                "extruder_b_start":
                {
                    "label": "Extruder B begin clamp",
                    "description": "The beginning percentage to start extruder b.",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "'b' in rotation_order and effect_type == 'effect'"
                },
                "extruder_b_end":
                {
                    "label": "Extruder B end clamp",
                    "description": "The ending percentage to start extruder b.",
                    "type": "float",
                    "default_value": 100,
                    "enabled": "'b' in rotation_order and effect_type == 'effect'"
                },
                "extruder_c_start":
                {
                    "label": "Extruder C begin clamp",
                    "description": "The beginning percentage to start extruder c.",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "'c' in rotation_order and effect_type == 'effect'"
                },
                "extruder_c_end":
                {
                    "label": "Extruder C end clamp",
                    "description": "The ending percentage to start extruder c.",
                    "type": "float",
                    "default_value": 100,
                    "enabled": "'c' in rotation_order and effect_type == 'effect'"
                },
                "extruder_d_start":
                {
                    "label": "Extruder D begin clamp",
                    "description": "The beginning percentage to start extruder d.",
                    "type": "float",
                    "default_value": 0,
                    "enabled": "'d' in rotation_order and effect_type == 'effect'"
                },
                "extruder_d_end":
                {
                    "label": "Extruder D end clamp",
                    "description": "The ending percentage to start extruder d.",
                    "type": "float",
                    "default_value": 100,
                    "enabled": "'d' in rotation_order and effect_type == 'effect'"
                },
                "change_rate":
                {
                    "label": "Effect Change frequency",
                    "description": "How many layers until the color is shifted each time.",
                    "unit": "#",
                    "type": "int",
                    "default_value": 4,
                    "minimum_value": "0",
                    "maximum_value": "1000",
                    "minimum_value_warning": "1",
                    "maximum_value_warning": "100",
                    "enabled": "effect_type == 'effect'"
                },
                "loop_type":
                {
                    "label": "Effect Loop Type",
                    "description": "::Linear: Start with primary extruder finish with last extruder. ::Circular: Start with primary extruder shift through to last extruder and then shift back to primary extruder",
                    "type": "enum",
                    "options": {"1":"Linear","0":"Circular"},
                    "default_value": "1",
                    "enabled": "effect_type == 'effect'"
                },
                "effect_modifier":
                {
                    "label": "Modifier Type",
                    "description": "::Normal: Sets the shift to change gradually throughout the length of the layers within the clamp. ::Wood Texture: Sets one extruder at a random small percentage and adjusts change frequency by a random amount, simulating wood grain. ::Repeating Pattern: Repeats a set extruder pattern throughout the print. ",
                    "type": "enum",
                    "options": {"normal":"Normal", "wood":"Wood Texture", "pattern":"Repeating Pattern", "random":"Random", "lerp":"Linear Interpolation", "slope":"Slope Formula", "ellipse":"Ellipse Formula"},
                    "default_value": "normal",
                    "enabled": "effect_type == 'effect'"
                },
                "rate_modifier":
                {
                    "label": "Rate Modifier Type",
                    "description": "How often the print shifts. ::Normal: Uses the change rate.  ::Random: picks a number of layers between the set change_rate and change_rate*2",
                    "type": "enum",
                    "options": {"normal":"Normal", "random":"Random"},
                    "default_value": "normal",
                    "enabled": "effect_type == 'effect'"
                },
                "lerp_i":
                {
                    "label": "Linear Interpolation",
                    "description": "Values shift up or down y axis.",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": "-1",
                    "maximum_value": "1",
                    "minimum_value_warning": "-0.9",
                    "maximum_value_warning": "0.9",
                    "enabled": "e_trigger == 'lerp' and effect_type == 'effect'"
                },
                "slope_m":
                {
                    "label": "Slope",
                    "description": "Slope (M) of the formula Y=MX+B. Normal range between -2 to 0. -1 is a one to one even slope. Values higher than -1 will start the shift later in the print. Values lower than -1 will start the print with a lower value for the primary extruder.",
                    "type": "float",
                    "default_value": -1,
                    "minimum_value": "-2",
                    "maximum_value": "0",
                    "minimum_value_warning": "-25",
                    "maximum_value_warning": "0.1",
                    "enabled": "e_trigger == 'slope' and effect_type == 'effect'"
                },
                "slope_i":
                {
                    "label": "Y Intercept",
                    "description": "Y Intercept (B) of the formula Y=MX+B. Normal range between 2 to 0. 1 is normal. Values lower than 1 will cause the primary extruder to retain 1 longer. Values higher than 1 will start out with primary extruder at a lower value, which will also run out sooner.",
                    "type": "float",
                    "default_value": 1,
                    "minimum_value": "0",
                    "maximum_value": "2",
                    "minimum_value_warning": "0.1",
                    "maximum_value_warning": "1.9",
                    "enabled": "e_trigger == 'slope' and effect_type == 'effect'"
                },
                "pattern":
                {
                    "label": "Pattern",
                    "description": "Set a repeating pattern of extruder values between 0 and 1.",
                    "type": "str",
                    "default_value": "0.5,1,0.25,0.75,0.5,0",
                    "enabled": "e_trigger == 'pattern' and effect_type == 'effect'"
                },
                "expert":
                {
                    "label": "Expert Controls",
                    "description": "Enable more controls. Some of which are for debugging purposes and may change or be removed later",
                    "type": "bool",
                    "default_value": false
                },
                "enable_initial":
                {
                    "label": "Enable Initial Setup",
                    "description": "If your extruder setup isn't set in the duet’s sd card settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "expert"
                },
                "initial_a":
                {
                    "label": "Define Tool",
                    "description": "Define Tool",
                    "type": "str",
                    "default_value": "M563 P0 D0:1 H1",
                    "enabled": "enable_initial"
                },
                "initial_b":
                {
                    "label": "Set Tool Axis Offsets",
                    "description": "Set Tool Axis Offsets",
                    "type": "str",
                    "default_value": "G10 P0 X0 Y0 Z0",
                    "enabled": "enable_initial"
                },
                "initial_c":
                {
                    "label": "Set Initial Tool Active",
                    "description": "Set Initial Tool Active",
                    "type": "str",
                    "default_value": "G10 P0 R120 S220",
                    "enabled": "enable_initial"
                },
                "initial_d":
                {
                    "label": "Turn On Tool Mixing For The Extruder",
                    "description": "Turn On Tool Mixing For The Extruder",
                    "type": "str",
                    "default_value": "M568 P0 S1",
                    "enabled": "enable_initial"
                },
                "initial_e":
                {
                    "label": "Extra GCode",
                    "description": "Any Extra Gcode To Run At Start Of Print.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_initial"
                }
            }
        }"""


    def execute(self, data: list):

        # Load all the settings
        firmware_type = str(self.getSettingValueByKey("firmware_type"))
        qty_extruders = int(self.getSettingValueByKey("qty_extruders"))
        affected_tool = int(self.getSettingValueByKey("affected_tool"))
        effect_type = str(self.getSettingValueByKey("effect_type"))
        unit_type = str(self.getSettingValueByKey("unit_type"))
        percent_change_start = float(self.getSettingValueByKey("percent_change_start") / 100)
        percent_change_end = float(self.getSettingValueByKey("percent_change_end") / 100)
        layer_change_start = int(self.getSettingValueByKey("layer_change_start"))
        layer_change_end = int(self.getSettingValueByKey("layer_change_end"))
        blend_values = [float(blend_values) for blend_values in self.getSettingValueByKey("blend_values").strip().split(',')]
        rotation_order = str(self.getSettingValueByKey("rotation_order"))
        extruder_a_start = float(self.getSettingValueByKey("extruder_a_start"))
        extruder_a_end = float(self.getSettingValueByKey("extruder_a_end"))
        extruder_b_start = float(self.getSettingValueByKey("extruder_b_start"))
        extruder_b_end = float(self.getSettingValueByKey("extruder_b_end"))
        extruder_c_start = float(self.getSettingValueByKey("extruder_c_start"))
        extruder_c_end = float(self.getSettingValueByKey("extruder_c_end"))
        extruder_d_start = float(self.getSettingValueByKey("extruder_d_start"))
        extruder_d_end = float(self.getSettingValueByKey("extruder_d_end"))
        change_rate = int(self.getSettingValueByKey("change_rate"))
        loop_type = str(self.getSettingValueByKey("loop_type"))
        effect_modifier = str(self.getSettingValueByKey("effect_modifier"))
        rate_modifier = str(self.getSettingValueByKey("rate_modifier"))
        lerp_i = float(self.getSettingValueByKey("lerp_i"))
        slope_m = float(self.getSettingValueByKey("slope_m"))
        slope_i = float(self.getSettingValueByKey("slope_i"))
        pattern = [float(pattern) for pattern in self.getSettingValueByKey("pattern").strip().split(',')]
        enable_initial = bool(self.getSettingValueByKey("enable_initial"))
        initial_a = str(self.getSettingValueByKey("initial_a"))
        initial_b = str(self.getSettingValueByKey("initial_b"))
        initial_c = str(self.getSettingValueByKey("initial_c"))
        initial_d = str(self.getSettingValueByKey("initial_d"))
        initial_e = str(self.getSettingValueByKey("initial_e"))


        current_position = 0
        end_position = 0
        index = 0
        has_been_run = 0

        #miso initialize
        tool = 0
        zpos = 0
        relative = False
        toolHistory = tool
        zposHistory = zpos
        relativeHistory = relative

        # Iterate through the layers
        for active_layer in data:

            # Remove the whitespace and split the gcode into lines
            lines = active_layer.strip().split("\n")

            modified_gcode = ""
            for line in lines:
                if ";LAYER_COUNT:" in line:
                    # FINDING THE ACTUAL AFFECTED LAYERS
                    total_layers = float(line[(line.index(':') + 1): len(line)])

                    # Calculate positions based on total_layers
                    if unit_type == 'percent':
                        start_position = int(int(total_layers) * float(percent_change_start))
                        end_position = int(int(total_layers) * float(percent_change_end))
                    # Clamp within range
                    if unit_type == 'layer_no':
                        start_position = int(clamp(layer_change_start, 0, total_layers))
                        end_position = int(clamp(layer_change_end, 0, total_layers))

                    modified_gcode += line  # list the initial line info

                # CHANGES MADE TO LAYERS THROUGH THE AFFECTED LAYERS
                else:

                    tool = Miso.Gcode.updateTool(line, tool)
                    #zpos = Miso.Gcode.updateZ(line, zpos, relative)
                    relative = Miso.Gcode.updateRelative(line, relative)

                    isDirty = tool != toolHistory or zpos != zposHistory or relative != relativeHistory
                    if isDirty and Miso.Gcode.isExtrude(line):
                        toolHistory = tool
                        zposHistory = zpos
                        relativeHistory = relative

                        modified_gcode += Miso.Gcode.formatMix(tool, zpos, total_layers) + "\n"
                    modified_gcode += line + " tool " + str(tool) + " zpos " + str(zpos) + " relative " + str(relative) + "\n"

            # REPLACE THE DATA
            data[index] = modified_gcode
            index += 1
        return data


# MODIFIERS FOR DIFFERENT EFFECTS ON EXTRUDERS
# SHIFTS AFFECT EXTRUDER RATIOS AND RETURN BOTH VALUES TOGETHER (X AND 1-X)
def standard_shift(numerator, denominator):
    return numerator/denominator, (denominator-numerator)/denominator


def wood_shift(min_percentage, max_percentage):
    random_value = random.uniform(min_percentage, max_percentage)
    return random_value, 1-random_value


def pattern_shift(list):
    value = list.pop()
    list.insert(0, value)
    return value, 1-value


def random_shift():
    random_value = random.uniform(0, 1)
    return random_value, 1-random_value


def slope_shift(x_numerator, x_denomerator, m_slope, y_intercept):
    y = (m_slope*x_numerator/x_denomerator)+y_intercept
    y = clamp(y, 0, 1)
    return 1-y, y


def lerp_shift(v0, v1, t, i):
    #answer = (1 - t) * v0 + t * (v1*(1+i))
    answer = 1
    return 1-answer, answer



def ellipse_shift(x):
    y = 4 - ((0.12*x*x) + (1.12 * x) + 2.78)
    y = clamp(y, 0, 1)
    y = pow(y, 0.5)
    y = clamp(y, 0, 1)  # This is unnecessary but here just as an in case.
    return 1-y, y


# RATES AFFECT FREQUENCY OF SHIFTS AND RETURN ONE VALUE
def standard_rate(rate):
    return rate


def random_rate(min_percentage, max_percentage):
    random_value = int(random.uniform(min_percentage, max_percentage))
    return random_value

class Miso:
    # Hash of ToolConfigurations
    # Allows extruder mixes to be assigned to different tools
    _toolConfigs = {}

    @staticmethod
    def setToolConfig(toolId, toolConfig):
        Miso._toolConfigs[toolId] = toolConfig

    @staticmethod
    def getToolConfig(toolId):
        if toolId in Miso._toolConfigs:
            return Miso._toolConfigs[toolId]
        return Miso.Tool() #default


    # Miso.Tool
    # Mix and gradient information for a specific tool
    # Example:
    #   toolConfig = Miso.Tool([mix1, mix2, ...])
    class Tool:
        def __init__(self, stops=None):
            stops = stops or [Miso.Mix()]
            self.stops = {}
            for stop in stops:
                self.stops[stop.zstop] = stop.mix

    # Miso.Mix
    # Mix information for a single stop (layer)
    # Z is expressed in percentage (0 to 1)
    # extruders is an array of percentages (0 to 1)
    class Mix:
        def __init__(self, mix=[1], zstop=0):
            self.mix = mix
            self.zstop = zstop

    # Miso.Gcode
    # Methods that help read and generate gcode
    class Gcode:
        _movecodes = re.compile('^\\s*(G0|G1).+Z(?P<distance>\\d+)\\b')
        _extrudecodes = re.compile('^\\s*(G0|G1|G2|G3).+(E|F)\\d+\\b')
        _toolcodes = re.compile('^\\s*T(?P<toolid>\\d+)\\b')
        _absolutecodes = re.compile('^\\s*G91\\b')
        _relativecodes = re.compile('^\\s*G90\\b')

        @staticmethod
        def updateRelative(line, current):
            if Miso.Gcode._relativecodes.match(line):
                return True
            if Miso.Gcode._absolutecodes.match(line):
                return False
            return current

        @staticmethod
        def updateTool(line, current):
            match = Miso.Gcode._toolcodes.search(line)
            if match:
                return int(match.group('toolid'))
            return current

        @staticmethod
        def updateZ(line, current, relative):
            match = Miso.Gcode._movecodes.search(line)
            if match and relative:
                change = float(match.group('distance'))
                return current + change
            if match:
                return float(match.group('distance'))
            return current

        @staticmethod
        def isExtrude(line):
            return Miso.Gcode._extrudecodes.match(line)

        @staticmethod
        def formatMix(tool, zpos, zmax):
            index = zpos / zmax
            mix = Miso.Gcode._calcMix(index, tool)
            for i in range(len(mix)):
                mix[i] = Miso.Gcode._formatNumber(mix[i])
            return 'M567 P' + str(tool) + ' E' + ':'.join(mix)

        @staticmethod
        def _calcMix(index, tool):
            segment = Miso.Gcode._calcSegment(index, tool)
            srange = segment.keys()
            if len(srange) == 0:
                return [1]
            if len(srange) == 1:
                return segment[srange[0]]
            index = (index - min(srange[0], srange[1])) / (max(srange[0], srange[1])-min(srange[0], srange[1]))
            mix = []
            start = segment[min(srange[0], srange[1])]
            end = segment[max(srange[0], srange[1])]
            for extruder in range(max(len(start), len(end))):
                svalue = len(start) < extruder and start[extruder] or 0
                evalue = len(end) < extruder and end[extruder] or 0
                mix.append((evalue - svalue) * index + svalue)
            return mix

        @staticmethod
        def _calcSegment(index, tool):  # NOTE: this will allow mixes that total more than 1
            stops = Miso.getToolConfig(tool).stops
            start = None
            end = None
            for stop in stops.keys():  # TODO: If stop is 0 there will be a bug
                start = stop <= index and (start != None and max(start, stop) or stop) or start
                end = stop >= index and (end != None and max(end, stop) or stop) or end
            segment = {}
            if start:
                segment[start] = stops[start]
            if end:
                segment[end] = stops[end]
            return segment

        @staticmethod
        def _formatNumber(value):
            value = str(value).strip()
            if re.match('^\\.', value):
                value = '0' + value
            filter = re.search('\\d+(\\.\\d{1,2})?', value)
            if not filter:
                return '0'
            return filter.string[filter.start():filter.end()]

