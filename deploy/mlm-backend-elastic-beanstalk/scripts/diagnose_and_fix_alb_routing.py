"""
AWS ALB Host-Based Routing Diagnostic & Fix Tool
Region: ap-south-1
ALB: awseb--AWSEB-o1HRYFBvinZL
Frontend Target: MyStatus-Frontend-prod (i-0ac25670dc1227e3c:80)
Backend Target: MyStatus-Backend-prod (i-087c7f42a18720cfd:80)
"""

import sys
import os
import json

try:
    import boto3
except ImportError:
    print("boto3 is required. Run: pip install boto3")
    sys.exit(1)

REGION = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")
ALB_NAME_SUBSTRING = "AWSEB-o1HRYFBvinZL"

def get_elbv2_client():
    return boto3.client("elbv2", region_name=REGION)

def inspect_alb():
    client = get_elbv2_client()
    print("=" * 80)
    print("1. DISCOVERING LOAD BALANCER & TARGET GROUPS")
    print("=" * 80)
    
    # 1. Find the ALB
    lbs = client.describe_load_balancers()["LoadBalancers"]
    target_lb = None
    for lb in lbs:
        if ALB_NAME_SUBSTRING.lower() in lb["LoadBalancerName"].lower():
            target_lb = lb
            break
            
    if not target_lb:
        print(f"Error: Could not find ALB with name containing '{ALB_NAME_SUBSTRING}'")
        print("Available load balancers:", [lb["LoadBalancerName"] for lb in lbs])
        return None, None
        
    lb_arn = target_lb["LoadBalancerArn"]
    print(f"ALB Found: {target_lb['LoadBalancerName']}")
    print(f"ALB ARN: {lb_arn}")
    print(f"DNS Name: {target_lb['DNSName']}")
    print(f"VPC ID: {target_lb['VpcId']}")
    
    # 2. Find Target Groups
    tgs = client.describe_target_groups(LoadBalancerArn=lb_arn)["TargetGroups"]
    print("\n" + "=" * 80)
    print("2. TARGET GROUPS & REGISTERED TARGETS")
    print("=" * 80)
    
    tg_map = {}
    for tg in tgs:
        tg_arn = tg["TargetGroupArn"]
        tg_name = tg["TargetGroupName"]
        tg_port = tg["Port"]
        tg_protocol = tg["Protocol"]
        print(f"\nTarget Group: {tg_name}")
        print(f"  ARN: {tg_arn}")
        print(f"  Port: {tg_port} / Protocol: {tg_protocol}")
        
        # Check targets
        health_res = client.describe_target_health(TargetGroupArn=tg_arn)
        print("  Registered Targets:")
        for th in health_res["TargetHealthDescriptions"]:
            target_id = th["Target"]["Id"]
            target_port = th["Target"]["Port"]
            state = th["TargetHealth"]["State"]
            reason = th["TargetHealth"].get("Reason", "N/A")
            desc = th["TargetHealth"].get("Description", "")
            print(f"    - Instance: {target_id}:{target_port} | Health: {state} ({reason} {desc})")
            
        tg_map[tg_name] = tg_arn

    # 3. Inspect Listeners & Rules
    listeners = client.describe_listeners(LoadBalancerArn=lb_arn)["Listeners"]
    print("\n" + "=" * 80)
    print("3. LISTENERS & HOST ROUTING RULES")
    print("=" * 80)
    
    for l in listeners:
        l_port = l["Port"]
        l_proto = l["Protocol"]
        l_arn = l["ListenerArn"]
        print(f"\n--- Listener: {l_proto}:{l_port} ({l_arn}) ---")
        print(f"Default Actions: {json.dumps(l['DefaultActions'], indent=2)}")
        
        rules = client.describe_rules(ListenerArn=l_arn)["Rules"]
        print(f"Configured Rules ({len(rules)} total):")
        for r in rules:
            prio = r["Priority"]
            is_default = r["IsDefault"]
            conds = r["Conditions"]
            actions = r["Actions"]
            print(f"  Rule Priority: {prio} (Default: {is_default})")
            print(f"    Conditions: {json.dumps(conds)}")
            print(f"    Actions: {json.dumps(actions)}")

    return lb_arn, tg_map

def fix_alb_routing(lb_arn, frontend_tg_arn, backend_tg_arn):
    client = get_elbv2_client()
    print("\n" + "=" * 80)
    print("4. APPLYING CANONICAL HOST-BASED ROUTING RULES")
    print("=" * 80)
    
    listeners = client.describe_listeners(LoadBalancerArn=lb_arn)["Listeners"]
    https_listener = None
    http_listener = None
    
    for l in listeners:
        if l["Port"] == 443:
            https_listener = l
        elif l["Port"] == 80:
            http_listener = l
            
    if not https_listener:
        print("Error: Port 443 HTTPS listener not found on ALB!")
        return
        
    https_arn = https_listener["ListenerArn"]
    print(f"HTTPS Listener ARN: {https_arn}")
    
    # 1. Update/Create Rule 1 for web.mystatusads333.com -> Frontend TG
    rules = client.describe_rules(ListenerArn=https_arn)["Rules"]
    
    # Check existing rules
    web_rule = None
    api_rule = None
    for r in rules:
        if r["IsDefault"]:
            continue
        for c in r.get("Conditions", []):
            if c.get("Field") == "host-header":
                values = c.get("Values", [])
                if any("web.mystatusads333.com" in v for v in values):
                    web_rule = r
                if any("api.mystatusads333.com" in v for v in values):
                    api_rule = r

    # Configure Rule 1: web.mystatusads333.com -> Frontend Target Group
    if web_rule:
        print(f"Updating existing web rule {web_rule['RuleArn']} -> Frontend TG")
        client.modify_rule(
            RuleArn=web_rule["RuleArn"],
            Conditions=[{"Field": "host-header", "Values": ["web.mystatusads333.com"]}],
            Actions=[{"Type": "forward", "TargetGroupArn": frontend_tg_arn}]
        )
    else:
        print("Creating Rule 1: web.mystatusads333.com -> Frontend TG (Priority 10)")
        client.create_rule(
            ListenerArn=https_arn,
            Priority=10,
            Conditions=[{"Field": "host-header", "Values": ["web.mystatusads333.com"]}],
            Actions=[{"Type": "forward", "TargetGroupArn": frontend_tg_arn}]
        )
        
    # Configure Rule 2: api.mystatusads333.com -> Backend Target Group
    if api_rule:
        print(f"Updating existing api rule {api_rule['RuleArn']} -> Backend TG")
        client.modify_rule(
            RuleArn=api_rule["RuleArn"],
            Conditions=[{"Field": "host-header", "Values": ["api.mystatusads333.com"]}],
            Actions=[{"Type": "forward", "TargetGroupArn": backend_tg_arn}]
        )
    else:
        print("Creating Rule 2: api.mystatusads333.com -> Backend TG (Priority 20)")
        client.create_rule(
            ListenerArn=https_arn,
            Priority=20,
            Conditions=[{"Field": "host-header", "Values": ["api.mystatusads333.com"]}],
            Actions=[{"Type": "forward", "TargetGroupArn": backend_tg_arn}]
        )

    # 2. Ensure HTTP :80 Redirects to HTTPS :443
    if http_listener:
        http_arn = http_listener["ListenerArn"]
        print(f"\nConfiguring HTTP :80 listener {http_arn} -> Redirect to HTTPS :443")
        client.modify_listener(
            ListenerArn=http_arn,
            DefaultActions=[{
                "Type": "redirect",
                "RedirectConfig": {
                    "Protocol": "HTTPS",
                    "Port": "443",
                    "Host": "#{host}",
                    "Path": "/#{path}",
                    "Query": "#{query}",
                    "StatusCode": "HTTP_301"
                }
            }]
        )

    print("\n" + "=" * 80)
    print("ROUTING RULES CONFIGURATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        lb_arn, tg_map = inspect_alb()
    except Exception as e:
        print(f"AWS Error: {e}")
