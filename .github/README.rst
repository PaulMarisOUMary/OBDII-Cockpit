OBDII-Cockpit
=============

A real-time OBDII dashboard, running on a Raspberry Pi with a DSI display.
Powered by `py-obdii <https://github.com/PaulMarisOUMary/OBDII>`_.

Originally a private personal project, now open-sourced. Runs daily in my own car.

.. image:: ../docs/cockpit-sim.png
    :alt: Dashboard simulator preview
    :width: 100%

.. image:: ../docs/cockpit.png
    :alt: Dashboard running in a real car
    :width: 33%

----

Features
--------

- Live display of speed, RPM, engine load, coolant temperature, oil temperature, and more
- Automatic blue light filter based on time of day
- Configurable polling frequency per OBD command
- Automatic reconnection on connection loss
- Rotating log files per session
- Development mode with simulator

Hardware
--------

- Raspberry Pi 3B+/CM4/CM5
- `Waveshare 7.9" DSI LCD <https://www.waveshare.com/7.9inch-dsi-lcd.htm>`_ (`Wiki <https://www.waveshare.com/wiki/7.9inch_DSI_LCD>`_)
- Any ELM327 compatible OBDII adapter (USB, WiFi, Bluetooth)


Raspberry Pi Setup
------------------

This guide explains how to setup a Raspberry Pi 3B+/CM4/CM5 with a Waveshare 7.9" DSI LCD and run a Python Pygame dashboard at boot, fully silent and fullscreen.

Prerequisites
^^^^^^^^^^^^^

Configure SSH, User (your_user) and WiFi before flashing the image.

Install Dependencies
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo apt update && sudo apt upgrade -y

.. code-block:: bash

    sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev -y
    sudo apt install python3-pygame -y

Add User to Video Group
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo usermod -aG video your_user

Create Project Directory & Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    mkdir ~/Dashboard
    python3 -m venv --system-site-packages ~/Dashboard/.venv
    source ~/Dashboard/.venv/bin/activate
    pip install -r requirements.txt

Configure Display
^^^^^^^^^^^^^^^^^

Edit `sudo nano /boot/firmware/config.txt`:

.. code-block:: ini

    # For more options and information see
    # http://rptl.io/configtxt
    # Some settings may impact device functionality. See link above for details

    # Uncomment some or all of these to enable the optional hardware interfaces
    #dtparam=i2c_arm=on
    #dtparam=i2s=on
    #dtparam=spi=on

    # Enable audio (loads snd_bcm2835)
    #dtparam=audio=on

    # Additional overlays and parameters are documented
    # /boot/firmware/overlays/README

    # Automatically load overlays for detected cameras
    #camera_auto_detect=1

    # Automatically load overlays for detected DSI displays
    display_auto_detect=1

    # Automatically load initramfs files, if found
    auto_initramfs=1

    # Enable DRM VC4 V3D driver
    dtoverlay=vc4-kms-v3d
    max_framebuffers=2

    # Don't have the firmware create an initial video= setting in cmdline.txt.
    # Use the kernel's default instead.
    disable_fw_kms_setup=1

    # Run in 64-bit mode
    arm_64bit=1

    # Disable compensation for displays with overscan
    disable_overscan=1
    disable_splash=1

    avoid_warnings=1

    # Run as fast as firmware / board allows
    arm_boost=1

    [cm4]
    # Enable host mode on the 2711 built-in XHCI USB controller.
    # This line should be removed if the legacy DWC2 controller is required
    # (e.g. for USB device mode) or if USB support is not required.
    otg_mode=1

    [cm5]
    dtoverlay=dwc2,dr_mode=host

    [all]
    dtoverlay=vc4-kms-dsi-waveshare-panel,7_9_inch

Edit `sudo nano /boot/firmware/cmdline.txt` (all on one line):

.. code-block:: text

    video=DSI-1:400x1280e,rotate=90 console=tty3 root=PARTUUID=8adb8d1c-02 rootfstype=ext4 fsck.repair=yes rootwait quiet fastboot splash loglevel=3 plymouth.ignore-serial-consoles vt.global_cursor_default=0 cfg80211.ieee80211_regdom=FR

- Keep your own `root=PARTUUID=8adb8d1c-02`
- Same thing for `cfg80211.ieee80211_regdom=FR`

Suppress Login Prompt
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo systemctl disable getty@tty1.service

Create Systemd Service for Dashboard
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File: `sudo nano /etc/systemd/system/obd-dashboard.service`

.. code-block:: ini

    [Unit]
    Description=OBDII Dashboard
    After=local-fs.target
    Requires=local-fs.target

    [Service]
    Type=simple
    User=your_user

    WorkingDirectory=/home/your_user/Dashboard
    ExecStart=/home/your_user/Dashboard/.venv/bin/python3 -OO main.py

    #Restart=always

    TTYPath=/dev/tty1
    TTYReset=yes
    TTYVHangup=yes

    StandardOutput=inherit
    StandardError=inherit

    [Install]
    WantedBy=multi-user.target

Splash Screen
^^^^^^^^^^^^^

.. code-block:: bash

    sudo apt install plymouth plymouth-themes

    sudo plymouth-set-default-theme spinner

    sudo nano /usr/share/plymouth/themes/spinner/spinner.plymouth

    # Edit: VerticalAlignment=.5

    sudo update-initramfs -u

Enable and Start Service
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    sudo systemctl daemon-reload
    sudo systemctl enable obd-dashboard.service
    sudo systemctl start obd-dashboard.service

Optimize Boot
^^^^^^^^^^^^^

See what services take time to start:

.. code-block:: bash

    systemd-analyze time

    systemd-analyze blame

    systemd-analyze critical-chain

    systemctl list-unit-files --state=enabled

.. code-block:: bash

    sudo systemctl disable NetworkManager-wait-online.service

    sudo systemctl disable bluetooth.service
    sudo systemctl disable hciuart.service

    sudo systemctl disable alsa-restore.service

    sudo systemctl disable ModemManager.service

    sudo systemctl disable rpi-eeprom-update.service
    sudo systemctl disable apt-daily.timer apt-daily-upgrade.timer

    sudo systemctl disable man-db.timer
    sudo systemctl disable sshswitch.service
    sudo systemctl disable avahi-daemon.service avahi-daemon.socket

    sudo systemctl disable fstrim.timer

    sudo systemctl disable console-setup.service
    sudo systemctl disable keyboard-setup.service

Related
-------

- `py-obdii <https://github.com/PaulMarisOUMary/OBDII>`_ (`pip <https://pypi.org/project/py-obdii/>`_) - the Python OBDII library powering this dashboard
- `ELM327-Emulator <https://pypi.org/project/ELM327-emulator>`_ - simulate a vehicle for development