# AWS EC2 Cost Reporter

A Python script that collects **EC2 instance, EBS volumes, and public IP usage** across AWS regions, then generates a CSV report with **monthly cost estimation**.

## Features
- Scans all AWS regions (or modify to specific ones)
- Reports:
  - Instance Name, Type, and Cost
  - Attached Disks (Name, Type, Size, Cost)
  - Public IPs (Elastic & Auto-assigned, Cost)
- Outputs a **CSV file** with a breakdown + total monthly cost
- Uses **on-demand pricing** defined in the script (customizable)

## Installation

## Clone this repo:

    git clone https://github.com/devopstechy/aws-cost-reporter.git
    cd aws-cost-reporter
## Install dependencies:
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
##  Configure AWS credentials (must have ec2:Describe* permissions):
    aws configure

## Usage

## Run the script:
    python cost_reporter.py
## This will generate with data:
    aws_instances_cost.csv

## Customization

    To limit regions, edit:
    regions = ["us-east-1", "ap-south-1"]    