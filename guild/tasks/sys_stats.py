from __future__ import division

import json
import sys
import time

import psutil

DEFAULT_INTERVAL = 1 # seconds

cpu_percent_init = False
last_disk = None

def start(op, stop, interval=DEFAULT_INTERVAL):
    _try_import_psutil()
    _loop(interval, stop)

def _loop(interval, stop):
    while True:
        if stop.poll(interval):
            stop.send("ack")
            break
        _log_sys_stats()

def _try_import_psutil():
    try:
        import psutil
    except ImportError:
        guild.log.warn(
            "WARNING: psutil not installed, cannot collect system stats "
            "(see https://github.com/giampaolo/psutil)\n")

def _log_sys_stats():
    _log_cpu_stats()

def _log_cpu_stats():
    stats = _cpu_stats()
    print("****", stats)

def _cpu_stats():
    global cpu_percent_init
    percents = psutil.cpu_percent(None, True)
    stats = {}
    if cpu_percent_init:
        i = 0
        for percent in percents:
            stats["sys/cpu%i/util" % i] = percent / 100
            i += 1
        stats["sys/cpu/util"] = sum(percents) / len(percents) / 100
    cpu_percent_init = True
    return stats

###################################################################
# Disk stats
###################################################################

def print_disk_stats():
    print_kv(disk_stats())

def disk_stats():
    global last_disk
    cur_disk = timed_disk_io_counters()
    stats = {}
    if last_disk:
        for dev_name, last, cur in zip_physical_disk_stats(last_disk, cur_disk):
            for stat_name, val in calc_disk_stats(last, cur).items():
                stats[dev_stat_key(dev_name, stat_name)] = val
    last_disk = cur_disk
    return stats

def timed_disk_io_counters():
    now = time.time()
    counters = psutil.disk_io_counters(True)
    for key, counts in counters.items():
        counts_dict = counts._asdict()
        counts_dict["timestamp"] = now
        counters[key] = counts_dict
    return counters

def zip_physical_disk_stats(all_last, all_cur):
    for device in psutil.disk_partitions():
        full_name = device.device
        if not full_name.startswith('/dev/'):
            raise AssertionError(full_name)
        name = full_name[5:]
        dev_last = all_last.get(name)
        dev_cur = all_cur.get(name)
        if dev_last and dev_cur:
            yield name, dev_last, dev_cur

def calc_disk_stats(last, cur):
    stats = {}
    seconds = cur["timestamp"] - last["timestamp"]
    writes = cur["write_count"] - last["write_count"]
    reads = cur["read_count"] - last["read_count"]
    bytes_written = cur["write_bytes"] - last["write_bytes"]
    bytes_read = cur["read_bytes"] - last["read_bytes"]
    stats["wps"] = writes / seconds
    stats["rps"] = reads / seconds
    stats["wkbps"] = bytes_written / 1024 / seconds
    stats["rkbps"] = bytes_read / 1024 / seconds
    try:
        busy_time_ms = cur["busy_time"] - last["busy_time"]
    except KeyError:
        pass
    else:
        stats["util"] = busy_time_ms / (seconds * 1000)
    return stats

def dev_stat_key(dev_name, stat_name):
    return "sys/dev%s/%s" % (dev_name, stat_name)

###################################################################
# Memory stats
###################################################################

def print_mem_stats():
    print_kv(mem_stats())

def mem_stats():
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "sys/mem/total": mem.total,
        "sys/mem/free": mem.free,
        "sys/mem/used": mem.used,
        "sys/mem/util": mem.percent / 100,
        "sys/swap/total": swap.total,
        "sys/swap/free": swap.free,
        "sys/swap/used": swap.used,
        "sys/swap/util": swap.percent / 100
    }

###################################################################
# Print
###################################################################

def print_kv(vals):
    json.dump({"kv": vals}, sys.stdout)
    print_eof()

def print_eof():
    sys.stdout.write("\n\n")
    sys.stdout.flush()

###################################################################
# Main
###################################################################

def main():
    while sys.stdin.readline():
        print_cpu_stats()
        print_disk_stats()
        print_mem_stats()
        print_eof()

def read_uptime():
    return float(open("/proc/uptime", "r").read().split()[0])
