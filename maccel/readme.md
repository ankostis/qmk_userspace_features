# Mouse acceleration

This feature was born from the frustration of not having a tweakable acceleration curve that could work between OSes and hosts and be specific to one device, catalysed by multiple users expressing interest.

## Installation

You have 2 options of how to build it.


**1. First build option:**



First copy the `maccel.c` and `maccel.h` files into your keymap folder.

Then simply add the following code at the top of your keymap.c file:
```c
#include "maccel.c"

report_mouse_t pointing_device_task_user(report_mouse_t mouse_report) {
    return pointing_device_task_maccel(mouse_report);
}
```

If you already have a `pointing_device_task_user` in your keymap, then add the `pointing_device_task_maccel` line to that instead.

This is an easy option if you are not maintaining a userspace.


**2. Second build option for those maintaining a user space:**


First copy the `maccel.c` and `maccel.h` files into your user space.

Then you can add the `maccel.c` to your build process by naming it in `rules.mk`: 
```
SRC += "maccel.c"
```

---

Next, add the acceleration shim to your `pointing_device_task_user`:
```c
report_mouse_t pointing_device_task_user(report_mouse_t mouse_report) {
    // ...
    return pointing_device_task_maccel(mouse_report);
}
```
If you have chosen to use the build system, you will also need to `#include "maccel.h`.

You may call it at the beginning if you wish to use the accelerated mouse report for your other code.

If you have not previously implemented a `pointing_device_task_user` (ie. your keymap has no such function), add one to `keymap.c`:
```c
report_mouse_t pointing_device_task_user(report_mouse_t mouse_report) {
    return pointing_device_task_maccel(mouse_report);
}
```

## Configuration

This accel curve works in opposite direction from what you may be used to from other acceleration tools, due to technical limitation in QMK. It scales pointer sensitivity upwards rather than downwards, which means you will likely have to lower your DPI setting from what you'd normally do.

Several characteristics of the acceleration curve can be tweaked by adding relevant defines to `config.h`:
```c
#define MACCEL_STEEPNESS 0.6 // steepness of accel curve
#define MACCEL_OFFSET 0.8    // start offset of accel curve
#define MACCEL_LIMIT 3.5     // upper limit of accel curve
```
[![](accel_curve.png)](https://www.wolframalpha.com/input?i=plot+c-%28c-1%29%28e%5E%28-%28x-b%29*a%29%29+with+a%3D0.6+with+b%3D0.8+with+c%3D3.5+from+x%3D-0.1+to+10+from+y%3D-0.1+to+4.5)

Interpret this graph as follows: horizontal axis is input velocity (ie. how fast you are physically moving your mouse/trackball/trackpad); vertical axis is the acceleration factor, which is the factor with which the input speed will be multiplied, resulting in your new output speed on screen. You can also understand this as a DPI scaling factor: at the start of the curve the factor is 1, and your mouse sensitivity will be equal to your default DPI setting. At the end of the curve, the factor approaches a limit which can be set by the LIMIT variable. The limit is 3.5 in this example and will result in a maximum mouse sensitivity of 3.5 times your default DPI.

The OFFSET variable moves the start of the curve towards the right, which means acceleration will kick in only after a certain velocity is reached. This is useful for low speed precision movements, in effect what you might normally use SNIPING mode for - and this is intended to entirely replace SNIPING mode. If you do not like this, you can set this variable to 0.

The STEEPNESS variable sets the steepness of the acceleration curve. A lower value will result in a flatter curve which takes longer to reach its LIMIT. A higher value will result in a steeper curve, which will reach its LIMIT faster.

A good starting point for tweaking your settings, is to set your default DPI to what you'd normally have set your sniping DPI. Then set the LIMIT variable to a factor that results in slightly higher than your usual default DPI. For example, if my usual settings are a default DPI of 1000 and a sniping DPI of 300, I would now set my default DPI to 300, and set my LIMIT variable to 3.5, which will result in an equivalent DPI scaling of 300*3.5=1050 at the upper limit of the acceleration curve. From there you can start playing around with the variables until you arrive at something to your liking.

To aid in dialing in the settings just right, a debug mode exists to print mathy details to the console. Refer to the QMK documentation on how to enable the console and debugging, then enable mouse acceleration debugging in `config.h`:
```c
#define MACCEL_DEBUG
/*
 * Requires enabling float support for printf!
 */
#undef PRINTF_SUPPORT_DECIMAL_SPECIFIERS
#define PRINTF_SUPPORT_DECIMAL_SPECIFIERS 1
```

The debug console will print your current DPI setting, the acceleration factor, the input velocity, and the accelerated velocity - which will help you understand what is happening at different settings of your variables.

## Limitations

With an unfavorable combination of `POINTING_DEVICE_THROTTLE_MS` and higher DPI, you may run into issues of peaking the maximum movement. Enable extended mouse reports by adding the following define in `config.h` to make this much less likely:
```c
#define MOUSE_EXTENDED_REPORT
```

The maccel feature has so far only been properly tested with PMW3360 sensor. However, it should work fine with all other QMK compatible sensors and devices as well, but the behaviour may not be 100% consistent across different DPI settings. Hence it might be a bit harder to dial in your variable preferences for those devices. This is due to a device-specific parameter in the calculations, that hasn't yet been determined for other devices than the PMW3360 sensor.

## Release history
- 2024 February 07 - Experimental new DPI correction to achieve consistent acceleration behavior across different user DPI settings.
- 2024 February 06 - First release candidate. Feedback welcome!

## Credits
Thanks to everyone who helped!
Including:
- Wimads (@wimads) and burkfers (@burkfers) wrote most of the code
- Quentin (@balanstik) for insightful commentary on the math, and testing
- ouglop (@ouglop) for insightful commentary on the math
- Drashna Jael're (@drashna) for coding tips and their invaluable bag of magic C tricks
