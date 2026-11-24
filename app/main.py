"""Створення QApplication і запуск головного вікна."""

import getpass
import sys

from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from app.theme import build_stylesheet, create_application_font
from app.ui.main_window import MainWindow

# Один процес на користувача: другий запуск лише просить перший показати вікно.
_SERVER_NAME = "ClipboardManager-" + "".join(
    char if char.isalnum() else "_" for char in getpass.getuser()
)


def _ask_running_instance_to_show() -> bool:
    """Повертає True, якщо вже працює процес із цією назвою."""
    socket = QLocalSocket()
    socket.connectToServer(_SERVER_NAME)
    if not socket.waitForConnected(1000):
        return False
    socket.write(b"show")
    socket.flush()
    socket.waitForBytesWritten(500)
    socket.disconnectFromServer()
    return True


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Clipboard Manager")
    app.setOrganizationName("ClipboardManager")
    app.setFont(create_application_font())
    app.setStyleSheet(build_stylesheet())
    # Вікно ховається в трей, тому вихід має бути явним (через меню трея).
    app.setQuitOnLastWindowClosed(False)

    server = QLocalServer()
    if not server.listen(_SERVER_NAME):
        if _ask_running_instance_to_show():
            return
        # Залишок від аварійно завершеного процесу — прибираємо й слухаємо знову.
        QLocalServer.removeServer(_SERVER_NAME)
        server.listen(_SERVER_NAME)

    window = MainWindow()
    window.show()

    def on_new_connection() -> None:
        while server.hasPendingConnections():
            socket = server.nextPendingConnection()
            socket.waitForReadyRead(100)
            socket.readAll()
            socket.disconnectFromServer()
            socket.deleteLater()
            window.show_window()

    server.newConnection.connect(on_new_connection)

    code = app.exec()
    server.close()
    QLocalServer.removeServer(_SERVER_NAME)
    sys.exit(code)


if __name__ == "__main__":
    main()
