#!/bin/bash
# KDC - Kawaii Distro Chooser
# detect_specs.sh — detects machine hardware specs and outputs JSON

get_cpu_info() {
    local cpu_model cores cpu_freq cpu_gen
    cpu_model=$(grep -m1 "model name" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | xargs)
    cores=$(grep -c "^processor" /proc/cpuinfo 2>/dev/null || echo "1")
    cpu_freq=$(grep -m1 "cpu MHz" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | xargs | cut -d. -f1)

    cpu_gen="modern"
    if echo "$cpu_model" | grep -qiE "Pentium|Celeron|Core 2|Atom"; then
        cpu_gen="old"
    elif echo "$cpu_model" | grep -qiE "i[357] [4-7][0-9]{3}|Ryzen [1-3]"; then
        cpu_gen="mid"
    fi

    echo "\"cpu_model\": \"${cpu_model:-Unknown}\", \"cpu_cores\": ${cores}, \"cpu_freq_mhz\": ${cpu_freq:-0}, \"cpu_gen\": \"${cpu_gen}\""
}

get_ram_info() {
    local total_kb total_mb
    total_kb=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
    total_mb=$((total_kb / 1024))
    echo "\"ram_mb\": ${total_mb:-0}"
}

get_gpu_info() {
    local gpu_vendor="unknown"
    local gpu_model="Unknown"

    if command -v lspci &>/dev/null; then
        local gpu_line
        gpu_line=$(lspci 2>/dev/null | grep -iE "VGA|3D|Display" | head -1)
        if echo "$gpu_line" | grep -qi "nvidia"; then
            gpu_vendor="nvidia"
        elif echo "$gpu_line" | grep -qi "amd\|radeon\|ati"; then
            gpu_vendor="amd"
        elif echo "$gpu_line" | grep -qi "intel"; then
            gpu_vendor="intel"
        fi
        gpu_model=$(echo "$gpu_line" | sed 's/.*: //' | xargs)
    fi

    echo "\"gpu_vendor\": \"${gpu_vendor}\", \"gpu_model\": \"${gpu_model}\""
}

get_disk_info() {
    local disk_gb
    disk_gb=$(df -BG / 2>/dev/null | awk 'NR==2 {gsub("G",""); print $2}')
    echo "\"disk_gb\": ${disk_gb:-0}"
}

get_bios_info() {
    local bios_type="legacy"
    if [ -d /sys/firmware/efi ]; then
        bios_type="uefi"
    fi
    echo "\"bios_type\": \"${bios_type}\""
}

get_current_os() {
    local os_name="Unknown"
    if [ -f /etc/os-release ]; then
        os_name=$(grep "^PRETTY_NAME" /etc/os-release | cut -d= -f2 | tr -d '"')
    fi
    echo "\"current_os\": \"${os_name}\""
}

echo "{"
echo "  $(get_cpu_info),"
echo "  $(get_ram_info),"
echo "  $(get_gpu_info),"
echo "  $(get_disk_info),"
echo "  $(get_bios_info),"
echo "  $(get_current_os)"
echo "}"
