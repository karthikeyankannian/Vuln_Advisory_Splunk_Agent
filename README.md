# Vuln_Advisory_Splunk_Agent

A small Splunk demo where **SPL decides vulnerability priority and an AI agent explains it**.

A Python script writes synthetic vulnerability findings. Splunk indexes them. SPL applies a four-rule priority policy and records which rule matched. A Splunk Agent Launchpad agent then turns that evidence into a plain-text analyst briefing. The agent never assigns a priority, never searches the index and never changes anything.

## Why it is built this way

When I first asked an LLM to explain a set of prioritised findings, it wrote well and got the facts wrong. It treated a "known exploited" flag as proof that the asset itself was compromised, guessed business functions from hostnames, and described a risk model that did not exist.

So the decision moved into SPL, where it is deterministic and testable, and the agent was left with one job: explain the evidence it is handed.

## How it flows

1. `generate_vulns.py` appends four synthetic findings to a local JSON file.
2. Splunk monitors the file and indexes the events.
3. SPL applies the `demo_v1` policy and records the matched rule and reason.
4. SPL packs the findings, counts and rule evidence into one row.
5. `aiagent` sends that row to the agent, which returns the briefing.

## Tested on

| Component | Version |
| --- | --- |
| Splunk Enterprise | 10.6.1.1, single instance on Linux |
| AI Toolkit | 6.2.0 |
| Splunk Cloud Connect | 1.1.4 |
| LLM connection | Splunk Hosted Models, OpenAI GPT-OSS 120B |

Agent Launchpad on an on-premises server needs Splunk Cloud Connect onboarding and the AI Toolkit feature activated for your tenant. That setup is not covered here; see the Splunk documentation linked at the end.

## Repository layout

```
generate_vulns.py                          Synthetic data generator
splunk_app/soc_agent_demo/local/           inputs.conf and props.conf
search/validation.spl                      Ingestion checks
search/vuln_priority_advisor.spl           Full end-to-end search
prompts/system_prompt.txt                  Agent system prompt
prompts/default_prompt.txt                 Agent default prompt
```

## Setup

All paths assume `SPLUNK_HOME=/opt/splunk`. Run the shell steps as the Linux user that runs Splunk.

1. Create the index `soc_agent_demo` under Settings, Indexes.

2. Create the data directory and copy the generator into it:

   ```bash
   mkdir -p /opt/splunk/var/log/soc_agent_demo
   cp generate_vulns.py /opt/splunk/var/log/soc_agent_demo/
   ```

3. Copy the app into place and restart Splunk:

   ```bash
   cp -r splunk_app/soc_agent_demo /opt/splunk/etc/apps/
   ```

   The monitor stanza points at the JSON file only, not at the directory that also holds the script.

4. Generate data and note the `run_id` it prints:

   ```bash
   python3 /opt/splunk/var/log/soc_agent_demo/generate_vulns.py
   ```

5. Run the two checks in `search/validation.spl`. You should see four events, four distinct findings, and one value per field.

6. In AI Toolkit, create an agent named `VulnPriorityAdvisor` on a supported LLM connection. Paste in `prompts/system_prompt.txt` and `prompts/default_prompt.txt`. Agent names are limited to 24 characters. Attach no MCP connection, knowledge base or skill.

7. Open `search/vuln_priority_advisor.spl`, replace `<RUN_ID_FROM_GENERATOR_OUTPUT>` with your `run_id`, and run it.

## The demo_v1 policy

Rules are evaluated in order and the first match wins. These are lab rules, not an approved production policy.

| Rule | Priority | Condition |
| --- | --- | --- |
| R1 | P1 | `known_exploited=yes` AND (`internet_facing=yes` OR `asset_criticality=critical`) |
| R2 | P2 | Remaining findings: `known_exploited=yes` OR (`cvss>=9` AND `internet_facing=yes`) |
| R3 | P3 | Remaining findings: `cvss>=7` |
| R4 | P4 | All remaining findings |

## Expected result

| Finding | Asset | CVSS | Rule | Priority |
| --- | --- | --- | --- | --- |
| DEMO-VULN-001 | demo-vpn01 | 9.8 | R1 | P1 |
| DEMO-VULN-002 | demo-payments01 | 8.1 | R1 | P1 |
| DEMO-VULN-003 | demo-web01 | 9.8 | R2 | P2 |
| DEMO-VULN-004 | demo-dev01 | 9.8 | R3 | P3 |

The search should return `status=success` with an empty `error` field. The briefing should attribute the priorities to upstream SPL and `demo_v1`, keep `exploitation_on_asset=not_assessed`, and label the evidence as synthetic.

## Things that tripped me up

- **Do not add `spath` to the searches.** `KV_MODE = json` already extracts the fields. A second extraction duplicates every value and makes four events look like eight.
- **"Unknown REST endpoint: agents" may not mean a missing endpoint.** On my server the handler existed and its import was failing on a missing Python module. Read the traceback first.
- **"Failed to create agent" in the UI may be wrong.** My agent reached READY in the backend about a minute later. Refresh the agent list before creating another one.
- **Replace old prompt instructions, do not append to them.** Leftover test instructions in the system prompt contradicted the new evidence and the agent followed the old ones.

## Where the data goes

Agent Launchpad runs the agent in Splunk Cloud Services, so the prompt leaves your server. In this demo the prompt includes the evidence string built by SPL. The index itself is not sent, because the agent has no search access. Read Splunk's data handling page and your own contract terms before using real data.

## Limits

- The data is synthetic. There are no real CVEs, asset owners or remediation deadlines.
- This is agent-assisted analysis. It is not live scanning, autonomous investigation or automated remediation.
- The policy is a demonstration and needs replacing with one your organisation has approved.

## References

- [AI Toolkit Agent Launchpad](https://help.splunk.com/en/splunk-cloud-platform/apply-machine-learning/use-ai-toolkit/6.2.0/ai-toolkit-connections-containers-and-agents/ai-toolkit-agent-launchpad)
- [Agent Launchpad for on-premises users](https://help.splunk.com/en/splunk-enterprise/apply-machine-learning/use-ai-toolkit/6.2.0/ai-toolkit-connections-containers-and-agents/agent-launchpad-for-on-premises-users)
- [Set up Splunk Cloud Connect](https://help.splunk.com/en/splunk-enterprise/splunk-cloud-connect/set-up-splunk-cloud-connect)
- [Connections in AI Toolkit](https://help.splunk.com/en/splunk-enterprise/apply-machine-learning/use-ai-toolkit/6.2.0/ai-toolkit-connections-containers-and-agents/connections-in-the-ai-toolkit)
