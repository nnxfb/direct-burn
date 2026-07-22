set ip [lindex $::argv 0]
set port [lindex $::argv 1]
set bit_path_remote [lindex $::argv 2]

open_hw_manager
connect_hw_server -url ${ip}:${port}
catch { close_hw_target }
open_hw_target
after 500
set devices [get_hw_devices]
if {[llength $devices] == 0} {
  puts "ERROR: No device detected"
  exit 1
}
refresh_hw_device -update_hw_probes false [lindex $devices 0]
after 300
set devices [get_hw_devices]
if {[llength $devices] == 0} {
  puts "ERROR: No device detected after refresh"
  exit 2
}
set target_dev [lindex $devices 0]
current_hw_device $target_dev
catch { open_hw_device $target_dev }
set bitfile "${bit_path_remote}"
if {![file exists $bitfile]} {
  puts "ERROR: Bitfile not found: $bitfile"
  exit 3
}
set_property PROGRAM.FILE $bitfile $target_dev
program_hw_devices $target_dev
close_hw_manager
exit 0
