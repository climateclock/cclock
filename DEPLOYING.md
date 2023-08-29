# Deployment procedure

This is the recommended procedure for deploying a new Action Clock.
It is important to carry out exactly these steps in this order
to guarantee that the clock's flash filesystem is intact and
ensure that all shipped clocks are in the same condition.

1. Fully assemble the Action Clock, ensuring the coin battery is installed.

2. Connect the charging adapter to the power port and let the clock charge up.

3. Ensure your phone has 4G coverage and use it to set up a Wi-Fi hotspot, with the name `climateclock` and password `climateclock`.

4. Turn the power dial fully left until it clicks into the off position.

5. Connect a USB cable from the MatrixPortal M4 board to your computer.

6. Double-press the RESET button on the MatrixPortal M4 board.  The LED on the M4 board should flash red and stay green.

7. You should see a MATRIXBOOT drive on your computer.  Drop the `erase.uf2` file on it.  Wait a few seconds until the LED on the M4 board flashes white and goes back to green.

8. Double-press the RESET button on the M4 board again.  The LED should flash red and go back to green.

9. The MATRIXBOOT drive should reappear on your computer.  Drop the `firmware.uf2` file on it.  Wait a few seconds until the LED on the M4 board flashes yellow and a CIRCUITPY drive appears on your computer.

10. Turn the power dial on.

11. Run the command `deploy -f v7` to deploy the current version (or replace `v7` with the current version).

12. Wait for the Action Clock to start up.  The deadline countdown will be incorrect, counting down from 29 years.

13. Disconnect the USB cable from your computer (not before this step!)

14. Wait for the clock to connect to your phone's hotspot.  Within a minute, it should get itself online and set its clock automatically.  The deadline should update according to the correct time.

15. Turn the power dial all the way off.

16. Your clock is ready to be shipped!
