from supportdesk.setup.file import create_supportdesk_folder


def after_migrate():
    create_supportdesk_folder()
