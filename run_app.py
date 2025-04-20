from frontend.app_client import AppClient
from lib import main_wrapper


@main_wrapper.main_wrapper
def main():
    main_wrapper.LIMIT_MEMORY_USAGE = False
    AppClient().run()


if __name__ == '__main__':
    main()
