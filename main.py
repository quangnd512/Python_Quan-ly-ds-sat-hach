# main.py - Điểm khởi đầu của ứng dụng
from controllers.app_controller import AppController
from views.app_view import AppView
from models.db import create_table
from models.db import migrate_old_db_if_exists

def main():
    migrate_old_db_if_exists()
    create_table()
    view = AppView()
    controller = AppController(view)
    view.set_controller(controller)
    view.setup_controller_commands()
    controller.show_data()
    view.run()

if __name__ == "__main__":
    main()