Raspberry Pi 7.9" DSI Dashboard Setup
=====================================

This guide explains how to setup a Raspberry Pi 3B+/CM4/CM5 with a Waveshare 7.9" DSI LCD
and run a Python Pygame dashboard at boot, fully silent and fullscreen.

Screen Reference
----------------
- Waveshare 7.9inch DSI LCD: https://www.waveshare.com/7.9inch-dsi-lcd.htm
- Documentation / Wiki: https://www.waveshare.com/wiki/7.9inch_DSI_LCD

Prerequisites
-------------
- Raspberry Pi OS Lite 64-bit installed
- User created for dashboard
- Wi-Fi configured
- SSH enabled

Update System
-------------
.. code-block:: bash

    sudo apt update && sudo apt upgrade -y

Install Dependencies
--------------------
.. code-block:: bash

    sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev -y
    sudo apt install python3-pygame -y

Add User to Video Group
-----------------------
.. code-block:: bash

    sudo usermod -aG video your_user

Create Project Directory & Virtual Environment
-----------------------------------------------
.. code-block:: bash

    mkdir ~/Dashboard
    python3 -m venv --system-site-packages ~/Dashboard/.venv
    source ~/Dashboard/.venv/bin/activate
    pip install -r requirements.txt

Configure Display
-----------------
Edit `/boot/firmware/config.txt`:

.. code-block:: ini

    [all]
    display_auto_detect=1
    auto_initramfs=1
    dtoverlay=vc4-kms-v3d
    max_framebuffers=2
    disable_fw_kms_setup=1
    arm_64bit=1
    disable_overscan=1
    disable_splash=1
    arm_boost=1
    avoid_warnings=1
    dtoverlay=vc4-kms-dsi-waveshare-panel,7_9_inch

Edit `/boot/cmdline.txt` (all on one line):

.. code-block:: text

    video=DSI-1:400x1280e,rotate=90 console=tty3 root=PARTUUID=... rootfstype=ext4 fsck.repair=yes rootwait quiet splash loglevel=3 plymouth.ignore-serial-consoles

- `rotate=90` rotates the screen
- `console=tty3` hides kernel messages from the DSI screen
- `quiet splash loglevel=3` suppresses boot messages

Suppress Login Prompt
---------------------
.. code-block:: bash

    sudo systemctl disable getty@tty1.service

Create Systemd Service for Dashboard
------------------------------------
File: `/etc/systemd/system/obd-dashboard.service`

.. code-block:: ini

    [Unit]
    Description=OBDII Dashboard
    After=network.target

    [Service]
    User=your_user
    WorkingDirectory=/home/your_user/Dashboard
    ExecStart=/home/your_user/Dashboard/.venv/bin/python3 main.py
    Restart=always
    StandardOutput=tty
    StandardError=tty
    TTYPath=/dev/tty1
    TTYReset=yes
    TTYVHangup=yes

    [Install]
    WantedBy=multi-user.target

Enable and Start Service
------------------------
.. code-block:: bash

    sudo systemctl daemon-reload
    sudo systemctl enable obd-dashboard.service
