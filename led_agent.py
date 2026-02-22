from dotenv import load_dotenv
import os
import json
import tempfile
import threading
from datetime import datetime, timezone
load_dotenv('.env')

from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage , HumanMessage, AIMessage

from langchain_openai import ChatOpenAI
# import importlib

LED_TO_GPIO_PIN = {
    "1": 17,
    "2": 27,
    "3": 22,
    "4": 23,
}

GPIO = None
GPIO_INIT_ERROR = None
OUTPUT_PATH = "output.json"
INITIAL_LED_STATE = {
    "leds": {"1": "off", "2": "off", "3": "off", "4": "off"},
    "updated_at": None,
}
LED_STATE_LOCK = threading.Lock()
LED_STATE = {
    "leds": dict(INITIAL_LED_STATE["leds"]),
    "updated_at": None,
}


def _load_led_state_into_memory() -> None:
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as file:
            loaded_state = json.load(file)
        if not isinstance(loaded_state, dict) or not isinstance(loaded_state.get("leds"), dict):
            return

        with LED_STATE_LOCK:
            LED_STATE["leds"].update(
                {str(key): value for key, value in loaded_state["leds"].items() if str(key) in LED_STATE["leds"]}
            )
            loaded_updated_at = loaded_state.get("updated_at")
            LED_STATE["updated_at"] = loaded_updated_at if isinstance(loaded_updated_at, str) else None
    except Exception:
        pass


def _persist_led_state() -> None:
    with LED_STATE_LOCK:
        state_snapshot = {
            "leds": dict(LED_STATE["leds"]),
            "updated_at": LED_STATE["updated_at"],
        }

    temp_file = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", dir=".")
    try:
        with temp_file:
            json.dump(state_snapshot, temp_file, indent=2)
        os.replace(temp_file.name, OUTPUT_PATH)
    except Exception:
        try:
            os.unlink(temp_file.name)
        except Exception:
            pass


def _update_led_state(led_id: str, state: str) -> None:
    with LED_STATE_LOCK:
        LED_STATE["leds"][led_id] = state
        LED_STATE["updated_at"] = datetime.now(timezone.utc).isoformat()

    _persist_led_state()


def _get_led_state_snapshot() -> dict:
    with LED_STATE_LOCK:
        return {
            "leds": dict(LED_STATE["leds"]),
            "updated_at": LED_STATE["updated_at"],
        }


_load_led_state_into_memory()

# try:
#     GPIO = importlib.import_module("RPi.GPIO")
#     GPIO.setmode(GPIO.BCM)
#     for gpio_pin in LED_TO_GPIO_PIN.values():
#         GPIO.setup(gpio_pin, GPIO.OUT)
# except Exception as gpio_error:
#     GPIO_INIT_ERROR = str(gpio_error)


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SYSTEM_MESSAGE = SystemMessage("""Your AI Controller for Home Lights, you will have tool to control
                               Home led you have to controll according to the user request, you can use the tools to control the led, don't choose any other things
                               """)


# @tool decorator to define a function as a tool automatically
@tool
def turn_on_led(led_number: int | str) -> str:
    """Turn ON a Raspberry Pi LED by LED id (1-4)."""
    # if GPIO is None:
    #     return f"GPIO initialization failed: {GPIO_INIT_ERROR}"

    led_id = str(led_number).strip()
    led_pin = LED_TO_GPIO_PIN.get(led_id)
    if led_pin is None:
        return "Invalid LED id. Use LED ids 1, 2, 3, or 4."

    # GPIO.output(led_pin, GPIO.HIGH)

    _update_led_state(led_id, "on")

    return f"LED {led_id} turned on at GPIO {led_pin}."


@tool
def turn_off_led(led_number: int | str) -> str:
    """Turn OFF a Raspberry Pi LED by LED id (1-4)."""
    # if GPIO is None:
    #     return f"GPIO initialization failed: {GPIO_INIT_ERROR}"

    led_id = str(led_number).strip()
    led_pin = LED_TO_GPIO_PIN.get(led_id)
    if led_pin is None:
        return "Invalid LED id. Use LED ids 1, 2, 3, or 4."

    # GPIO.output(led_pin, GPIO.LOW)

    _update_led_state(led_id, "off")

    return f"LED {led_id} turned off at GPIO {led_pin}."


@tool
def get_led_status() -> str:
    """Get current status of all LEDs (1-4)."""
    led_state = _get_led_state_snapshot()
    return json.dumps(led_state)





model = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)
agent_tools = [turn_on_led, turn_off_led, get_led_status]
# it uses react framework by default
agent = create_agent(
    model=model,
    tools=agent_tools,
    system_prompt=SYSTEM_MESSAGE,
    debug=False,
)

# Send a human message to the agent and print the final reply
chat_history: list[HumanMessage | AIMessage] = []

while True:
    query = input("Enter your query: ")
    led_state_memory = _get_led_state_snapshot()
    state_memory_message = SystemMessage(
        content=f"Current LED memory state: {json.dumps(led_state_memory)}"
    )

    response = agent.invoke(
        {"messages": [state_memory_message, *chat_history, HumanMessage(content=query)]}
    )
    assistant_reply = response["messages"][-1].content
    print(assistant_reply)

    chat_history.append(HumanMessage(content=query))
    chat_history.append(AIMessage(content=str(assistant_reply)))
