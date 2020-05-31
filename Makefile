dwm-monitor: monitor.py
	pyinstaller --hidden-import=pkg_resources.py2_warn -F -n dwm-monitor monitor.py
