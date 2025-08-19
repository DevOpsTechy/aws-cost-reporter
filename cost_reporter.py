import boto3
import csv

# ---------- Pricing (simplified) ----------
INSTANCE_PRICES = {
    "t3.micro": 0.006600,
    "t3.small": 0.013200,
    "t3.medium": 0.026400,
    "t3.large": 0.052800,
    "t3.2xlarge": 0.211100,
    "t2.small": 0.014600,
    "m5.large": 0.061000,
    "m5.2xlarge": 0.244000,
    "r5.large": 0.074000,
    "c5a.2xlarge": 0.189000,
    "c7g.8xlarge": 0.648000,
    "g4dn.2xlarge": 0.435000,
}
EBS_PRICES = {
    "gp2": 0.11,
    "gp3": 0.088,
    "io1": 0.125,
    "st1": 0.045,
    "sc1": 0.0168,
}
EIP_PRICE = 3.65  # per month (for every public IP, elastic or auto-assigned)
HOURS_IN_MONTH = 730

# ---------- Collect data ----------
ec2 = boto3.client("ec2")
regions = [r["RegionName"] for r in ec2.describe_regions()["Regions"]]

rows = []
total_cost = 0.0

for region in regions:
    print(f"Processing region: {region}")
    client = boto3.client("ec2", region_name=region)
    ec2r = boto3.resource("ec2", region_name=region)

    for instance in ec2r.instances.all():
        # Instance name
        instance_name = ""
        for tag in instance.tags or []:
            if tag["Key"] == "Name":
                instance_name = tag["Value"]

        inst_type = instance.instance_type
        inst_price_hr = INSTANCE_PRICES.get(inst_type, 0)
        inst_monthly_cost = round(inst_price_hr * HOURS_IN_MONTH, 2)

        # Collect disks
        disks = []
        for bd in instance.block_device_mappings:
            vol_id = bd["Ebs"]["VolumeId"]
            vol = ec2r.Volume(vol_id)
            vol_type = vol.volume_type
            vol_size = vol.size
            vol_name = ""
            for tag in vol.tags or []:
                if tag["Key"] == "Name":
                    vol_name = tag["Value"]
            price_gb = EBS_PRICES.get(vol_type, 0)
            vol_monthly = round(price_gb * vol_size, 2)
            disks.append((vol_name, vol_type, vol_size, vol_monthly))

        # Collect public IPs
        eips = []
        for ni in instance.network_interfaces:
            if ni.association_attribute and "PublicIp" in ni.association_attribute:
                public_ip = ni.association_attribute["PublicIp"]
                ip_name = ni.association_attribute.get("IpOwnerId", "")
                ip_cost = EIP_PRICE  # Always charge

                try:
                    addrs = client.describe_addresses(PublicIps=[public_ip]).get("Addresses", [])
                    if addrs:
                        for tag in addrs[0].get("Tags", []):
                            if tag["Key"] == "Name":
                                ip_name = tag["Value"]
                except client.exceptions.ClientError:
                    pass  # not elastic ip, ignore

                eips.append((public_ip, ip_name, ip_cost))

        # Ensure at least one disk & one IP placeholder so we can align columns
        max_len = max(len(disks), len(eips), 1)

        for i in range(max_len):
            row = []
            if i == 0:
                row.extend([region, instance_name, inst_type, inst_monthly_cost])
                total_cost += inst_monthly_cost
            else:
                row.extend(["", "", "", ""])

            # Disk info
            if i < len(disks):
                d = disks[i]
                row.extend([d[0], d[1], d[2], d[3]])
                total_cost += d[3]
            else:
                row.extend(["", "", "", ""])

            # IP info
            if i < len(eips):
                e = eips[i]
                row.extend([e[0], e[1], e[2]])
                total_cost += e[2]
            else:
                row.extend(["", "", ""])

            rows.append(row)

# ---------- Write CSV ----------
with open("aws_instances_cost.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "Region",
        "Instance Name",
        "Instance Type",
        "Instance Monthly Cost ($)",
        "Disk Name",
        "Disk Type",
        "Disk Size (GB)",
        "Disk Monthly Cost ($)",
        "Public IP",
        "IP Name",
        "IP Monthly Cost ($)"
    ])
    writer.writerows(rows)

# Add total row
with open("aws_instances_cost.csv", "a", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([])
    writer.writerow(["", "", "", "", "", "", "", "", "", "Total Cost ($)", round(total_cost, 2)])

print("CSV file 'aws_instances_cost.csv' generated successfully.")
