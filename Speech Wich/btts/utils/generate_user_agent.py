from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

def generate_user_agent():
    software_names = [
        SoftwareName.CHROME.value, SoftwareName.OPERA.value,
        SoftwareName.FIREFOX.value
    ]
    operating_systems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
    return UserAgent(software_names=software_names,
                     operating_systems=operating_systems,
                     limit=100).get_random_user_agent()