import configparser
from Website import create_app, colorama
import configparser, os, socket
from colorama import Fore, Style, Back

colorama.init(autoreset=True)
config = configparser.ConfigParser()
config_path = "config.txt"
yes_or_no_prompt = ("Y", "y", "N", "n")
yes_or_no_print = "(" + Fore.YELLOW + "Y" + Fore.RESET + "/" + Fore.YELLOW + "N" + Fore.RESET + "?): "


def print_blank():
    print(" ")


def configerror():
    # If the app is unable to parse the data in the config file,
    # prompts the error to the user and removing the config file
    print("Configuration File May Be Corrupted! " + Fore.RED + "[ERROR]")
    print("Resetting config file...")
    os.remove(config_path)  # Remove the config file
    print("Please Start the Server Again.")
    print("Shutting Down...")
    exit()


def prompt_configurations(install_method, write_method):  # Prompts for user value while setting up the config file
    print("Prompting for Configuration Values... ")
    config['Configurations'] = {}
    Configurations = config['Configurations']
    if install_method == "1":  # Setup with easy mode, app will ask for choice for each setting
        print("[" + Fore.BLUE + "Express Installation" + "]")
        self_ip = socket.gethostbyname_ex(socket.gethostname())
        print("Fetching ALL Ip Addresses from all interfaces on this machine...")
        print("Which one of the IP Addressess below is your current network interface?")
        ipcount = 1
        for ip in self_ip[2]:
            print(str(ipcount) + ". " + str(ip))
            ipcount += 1
        while True:
            try:
                ip_choice = int(input("Choice: "))
                while not 0 < ip_choice < (len(self_ip[-1]) + 1):
                    ip_choice = int(input("Choice: "))
                break
            except ValueError:
                print("Enter from the choices above")
        selected_ip = self_ip[2][ip_choice - 1]
        Configurations['host'] = selected_ip
        print("Selected IP Address (" + Fore.YELLOW + str(selected_ip) + Fore.RESET + ").")
        Configurations['port'] = '5000'
        Configurations['secret_key'] = 'laizhen828'
        mysql_where_question = "Is the MySQL Server Running on this machine?" + yes_or_no_print
        mysql_where = input(mysql_where_question)
        while mysql_where not in yes_or_no_prompt:
            mysql_where = input(mysql_where_question)
        if mysql_where == "Y" or mysql_where == "y":
            mysql_use_self = input("Shall we connect to the MySQL using the IP above?" + yes_or_no_print)
            while mysql_use_self not in yes_or_no_prompt:
                mysql_use_self = input("Shall we connect to the MySQL using the IP above?" + yes_or_no_print)
            if mysql_use_self == "Y" or mysql_use_self == "y":
                print("Using (" + Fore.YELLOW + selected_ip + Fore.RESET + ") as MySQL Host.")
                Configurations['mysql_host'] = str(selected_ip)
            else:
                ipcount = 1
                for ip in self_ip[-1]:
                    print(str(ipcount) + ". " + str(ip))
                    ipcount += 1
                while True:
                    try:
                        ip_choice = int(input("Choice: "))
                        while not 0 < ip_choice < (len(self_ip[-1]) + 1):
                            ip_choice = int(input("Choice: "))
                        break
                    except ValueError:
                        print("Enter from the choices above")
                selected_ip = self_ip[-1][ip_choice - 1]
                Configurations['mysql_host'] = selected_ip
        else:
            Configurations['mysql_host'] = input("Enter the IP Number of MySQL Server: ")
        input_mysql_port = input(
            "Enter the Port Number of MySQL Server (Press ENTER to use default value: " + Fore.YELLOW + "3306" + Fore.RESET + "): ")
        if len(input_mysql_port) == 0:
            Configurations['mysql_port'] = '3306'
            print("Using default values for MySQL Port (" + Fore.YELLOW + "3306" + Fore.RESET + ")")
        print("Using default values for Mysql User (" + Fore.YELLOW + "rfidwebapp" + Fore.RESET + ")")
        Configurations['mysql_user'] = 'dbadmin'
        print("Using default values for Mysql Password (" + Fore.YELLOW + "rfid12345" + Fore.RESET + ")")
        Configurations['mysql_password'] = 'dbadmin123'
        print("Using default values for Mysql Database Name (" + Fore.YELLOW + "rfid" + Fore.RESET + ")")
        Configurations['mysql_db_name'] = 'gcs_rbms'
    elif install_method == "2":
        print("[" + Fore.BLUE + "Custom Installation" + "]")
        Configurations['host'] = input("Enter Host IP: ")
        Configurations['port'] = input("Enter Host Port: ")
        Configurations['secret_key'] = input("Enter Secret Key: ")
        Configurations['mysql_user'] = input("Enter MySQL User: ")
        Configurations['mysql_password'] = input("Enter MySQL Password: ")
        Configurations['mysql_host'] = input("Enter MySQL Host: ")
        Configurations['mysql_port'] = input("Enter MySQL Port: ")
        Configurations['mysql_db_name'] = input("Enter MySQL Database Name: ")
    with open("config.txt", write_method) as f:
        config.write(f)
    f.close()
    return


def config_corrupted():
    # print("main no section")
    print("Config File may be corrupted." + Fore.RED + "[X]")
    print("How do you want to repair the file?")
    print("1. Delete config file & perform first time setup with express installation.")
    print("2. Re-enter each config values.")
    corrupted_choice = input("Repair Method: ")
    while corrupted_choice not in ("1", "2"):
        corrupted_choice = input("Repair Method: ")
    if corrupted_choice == "1":
        prompt_configurations("1", "a")
        print_blank()
    elif corrupted_choice == "2":
        prompt_configurations("2", "w")
        print_blank()
    return check_configurations()


def check_configurations():
    conf = {}
    prompt_installation_msg = "Please Select Installation Method (" + Fore.GREEN + "1" + Fore.RESET + "/" + Fore.LIGHTRED_EX + "2" + Fore.RESET + "): "
    if os.path.exists(config_path):
        print("Config File Exists. " + Fore.GREEN + "[OK]")
        print_blank()
        # print("main has file")
        try:
            config.read("config.txt")
        except:
            return config_corrupted()
        if config.has_section("Configurations"):
            try:
                # print("main has section")
                print("Running with Pre-saved Configurations.")
                conf['host'] = config.get('Configurations', 'host')
                conf['port'] = config.get('Configurations', 'port')
                conf['secret_key'] = config.get('Configurations', 'secret_key')
                conf['mysql_user'] = config.get('Configurations', 'mysql_user')
                conf['mysql_password'] = config.get('Configurations', 'mysql_password')
                conf['mysql_host'] = config.get('Configurations', 'mysql_host')
                conf['mysql_port'] = config.get('Configurations', 'mysql_port')
                conf['mysql_db_name'] = config.get('Configurations', 'mysql_db_name')
                # print(host, port, secret_key, mysql_user, mysql_password, mysql_host, mysql_port, mysql_db_name)
                return conf
            except:
                return config_corrupted()
        else:
            return config_corrupted()
    else:
        # print("main no file")
        print("Config File does not exist. " + Fore.RED + "[X]")
        print("Performing first time setup...")
        print_blank()
        print("[" + Fore.BLUE + "First Time Setup" + Fore.RESET + "]")
        print("1. Express Installation (" + Fore.GREEN + "Faster" + Fore.RESET + ")")
        print("2. Custom Installation (" + Fore.LIGHTRED_EX + "For advanced users" + Fore.RESET + ")")
        setup_option = input(prompt_installation_msg)
        while setup_option not in ("1", "2"):
            setup_option = input(prompt_installation_msg)
        print_blank()
        prompt_configurations(setup_option, "a")
        print_blank()
        return check_configurations()


print("[" + Fore.CYAN + "Room Booking Management System" + Fore.RESET + "]")
print("Loading Settings...")

conf = check_configurations()
app = create_app(conf)
if __name__ == '__main__':
    try:
        app.run(host=conf['host'], port=conf['port'], debug=True, use_reloader=False)
    except:
        print_blank()
        print("Unable to start the server on (" + Fore.MAGENTA + conf['host'] + Fore.RESET + ":" + Fore.MAGENTA + conf['port'] +
              Fore.RESET + ") [" + Fore.RED + "ERROR" + Fore.RESET + "]")
        print(Fore.YELLOW + "Make sure your configurations are correct.")
        exit()