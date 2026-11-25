# Game day: revise, then survive six incidents

[Course README](../README.md)

No new theory today. The class already knows containers, CI/CD, Kubernetes and high availability; now
they **use** it. First a quick revision to make sure the fundamentals are solid, then real outage stories
where the students are the on-call engineers.

## The plan (about 90 minutes)

| Time | Part | What happens |
|:---:|---|---|
| 0-20 min | [Part 1: Quick revision](1-quick-revision.md) | 15 rapid-fire questions: containers, CI/CD, GitOps, single points of failure, Kubernetes. Hands up, then reveal. |
| 20-80 min | [Part 2: Incident theater](2-incident-theater.md) | 6 true incidents, about 10 minutes each: the story, the room diagnoses, a hint, then the reveal. |
| 80-90 min | [Your turn](2-incident-theater.md#your-turn-last-10-minutes) | Students share their own worst bug, and which habit would have saved them. |

## How to run it

- Project these pages straight from GitHub. Every answer is hidden behind a click (**Answer**, **Hint**,
  **What really happened**), so you reveal it only when the room has had its say.
- Read questions aloud and wait. If nobody talks for 20 seconds, ask a yes/no question ("Is it the
  network? Is it the server?").
- Optional: two teams (left and right of the room), with points on the board.
- Incidents 1-3 happened to **us** while building this course; incidents 4-6 made world news. The first
  one happened to the instructor last week, so it's a good, light start.

## If you need a refresher yourself

- [Containers and Docker](../docs/containers-and-docker.md), the 9 slides
- [The deployment journey](../stages/README.md), Docker stages 1-5
- [Kubernetes concepts](../kubernetes/concepts.md) and the [Kubernetes stages](../kubernetes/README.md)

**Start:** [Part 1: Quick revision →](1-quick-revision.md)
