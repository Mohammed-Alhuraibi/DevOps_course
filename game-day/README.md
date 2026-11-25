# Game day: revise, then survive six incidents

[Course README](../README.md)

No new theory today. The class already knows containers, CI/CD, Kubernetes and high availability; now
they **use** it. First a quick revision to make sure the fundamentals are solid, then real outage stories
where the students are the on-call engineers.

## The plan (about 90 minutes)

| Time | Part | What happens |
|:---:|---|---|
| 0-20 min | [Part 1: Quick revision](1-quick-revision.md) | 17 rapid-fire questions: containers, CI/CD, GitOps, single points of failure, Kubernetes, secrets and infrastructure as code. Hands up, then reveal. |
| 20-80 min | [Part 2: Incident theater](2-incident-theater.md) | 6 true incidents, each about one DevOps practice, about 10 minutes each: the story step by step, the room diagnoses, a hint, then the answer. |
| 80-90 min | [Your turn](2-incident-theater.md#your-turn-last-10-minutes) | Which of the six habits is missing in your own project, and how would you add it? |

## How to run it

- Project these pages straight from GitHub. Nothing gives the answer away: every story step, hint and
  answer is hidden behind a click, so the room only sees what you have opened.
- Read aloud and wait. Students may ask you anything, but you answer only **yes or no**. If nobody talks
  for 20 seconds, ask one yourself ("Is it the network? Is it the server?").
- Two teams (left and right of the room), points on the board. In each incident, each team picks an
  **incident commander** (decides what to try next), a **comms person** (tells "the customers" what is
  going on in one sentence) and a **scribe** (writes the timeline on the board).
- Short on time? Incident 6 (Binance) needs about 15 minutes. Skip incident 3 (CrowdStrike) and mention
  its lesson in the wrap-up: ship to a few machines first (a canary), and stop automatically at the first
  sign of trouble.
- Incident 1 happened to **us** while building the Kubernetes lesson; incidents 2-6 made world news
  (Knight Capital, CrowdStrike, GitLab, tj-actions, Binance).

## If you need a refresher yourself

- [Containers and Docker](../docs/containers-and-docker.md), the 9 slides
- [The deployment journey](../stages/README.md), Docker stages 1-5
- [Kubernetes concepts](../kubernetes/concepts.md) and the [Kubernetes stages](../kubernetes/README.md)

**Start:** [Part 1: Quick revision →](1-quick-revision.md)
