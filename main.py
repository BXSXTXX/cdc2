from src import bot
from dotenv import load_dotenv
import sys

def check_version() -> None:
    import pkg_resources
    import src.log

    load_dotenv()
    logger = src.log.setup_logger(__name__)

    with open('requirements.txt') as f:
        required = f.read().splitlines()
    for package in required:
        package_name, package_version = package.split('==')
        installed = pkg_resources.get_distribution(package_name)
        name, version = installed.project_name, installed.version
        if package != f'{name}=={version}':
            logger.error(f'{name} version {version} ist installiert aber stimmt nicht mit den Anforderungen überein.')
            sys.exit()

if __name__ == '__main__': 
    check_version()
    bot.run_discord_bot()
    
