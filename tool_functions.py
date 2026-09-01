import subprocess
import sqlite3
import time
import colorsys
import dotenv
dotenv.load_dotenv(override=True)

import tinytuya
light = tinytuya.OutletDevice('a36cb72d1945cf9235fcsy', '192.168.1.2', 'Ke;0MYt#GGtwb?+u')
light.set_version(3.5) 

from tavily import TavilyClient
tavily_client = TavilyClient(api_key="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")

#===========================================================================================#

def run_shell(command):
    result = subprocess.run(command,shell=True,capture_output=True,text=True,timeout=5)
    return result.stdout + result.stderr

def view_reminders():
    conn = sqlite3.connect("memory/reminders.db",timeout=5)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM reminders").fetchall()
    output = ""
    for row in rows:
        local_time = time.localtime(row['trigger_time'])
        output += f"{row['content']} in {time.strftime("%I:%M %p, %b %d %Y",local_time)} \n"

    conn.close()

    output = "No reminders set" if output == "" else output
    return output

def manage_reminders(args):
    conn = sqlite3.connect("memory/reminders.db",timeout=5)
    action = args["action"]
    match action:

        case "create":
             conn.execute("""
                 INSERT INTO reminders (content, trigger_time)
                 VALUES (?, ?)
             """,
                (args["content"], int(time.time()) + args["trigger_time"])
            )
             conn.commit()

        case "finish":
            conn.execute("DELETE FROM reminders WHERE content LIKE ?", (f"%{args["content"]}%",))
            conn.commit()

    conn.close()
    return args["action"] + " reminder: " + args["content"]

def web_search(query):
    response = tavily_client.search(query,max_results=3,search_depth="advanced")
    output = ""
    for result in response["results"]:
        output+= result["title"] + "\n"
        output+= result["url"] + "\n"
        output+=result["content"][:350].replace("\n","") + "..." + "\n"
        output+="=======================" + "\n"
    print(output)
    return output


import colorsys
def rgbhex_to_huesat(hex_color):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    hue = int(h * 360)
    sat = int(s * 1000)
    return f"{hue:04x}{sat:04x}"

# on or off         (20)  :   True/False
# mode              (21)  :   'white'/'colour'
# white brightness  (22)  :   (0,1000)
# temp color        (23)  :   (0,1000)
# hue, sat, bright  (24)  :   [0:4] + [4:8] + [8:12] (naka hexadecimal format)
def control_light(args):
    try:
        status = light.status()['dps']
        #============================================================================#
        if args.get("switch_led") is not None:
            light.set_status(args["switch_led"], '20')
        #============================================================================#
        if args.get("temp_value") is not None:
            light.set_value('21', 'white') #para sa white mode lang ang temp settings

            light.set_value('23', args['temp_value'])
        #============================================================================#
        if args.get("colour_data"):
            light.set_value('21', 'colour')
            hue_sat = rgbhex_to_huesat(args["colour_data"])

            current_bright_hex = ""
            if status['21'] == "white":
                current_bright_hex = format(status.get('22'), '04x')
            elif status['21'] == "colour":
                current_bright_hex = status['24'][8:]

            light.set_value('24', hue_sat + current_bright_hex)
        #============================================================================#
        if args.get("bright_value") is not None:
            status = light.status()['dps']
            match status['21']:   # colour mode o white mode?

                case 'colour':
                    hue_sat = status['24'][:8]   # current hue + sat
                    bright_value = format(args['bright_value'], '04x') 
                    light.set_value( '24', hue_sat + bright_value )

                case 'white':
                    light.set_value('22', args["bright_value"])
                    
        #============================================================================#
        print(args)
        return "success"

    except Exception as e:
        print(e)
        return str(e)