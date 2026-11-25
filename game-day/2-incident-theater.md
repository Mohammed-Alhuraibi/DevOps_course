# Part 2: Incident theater (about 60 minutes)

[Game day](README.md) · [← Part 1: Quick revision](1-quick-revision.md) · **Part 2: Incident theater**

Six true incidents. One happened to us while building this course; five made world news. **You are the
on-call engineer.**

**Every incident works the same way:**

1. **The setting** is visible: who, and what they were doing.
2. **What happened** is hidden: open one step at a time and read it aloud.
3. **Your call:** the room diagnoses out loud. Guess, argue, ask questions back.
4. **Hint:** if the room is stuck after 30 seconds.
5. **The answer:** the root cause, the fix, the DevOps practice, and where it is in our course.

> [!TIP]
> Two teams (left and right of the room), points on the board: one for the right cause, one for a good
> fix. The narrator answers only **yes or no** questions ("Was it the network?" "No."). No googling.

---

## Incident 1: The update that dropped requests

*Happened to us while building the Kubernetes lesson.*

**The setting.** Bug Squash runs on Kubernetes (GKE) with 3 frontend pods behind Google's load
balancer. We ship a new version while a loop sends one request per second, to prove that nobody notices.

<details><summary><b>Step 1</b>: the update starts</summary>

`kubectl set image` starts a rolling update: pods are replaced one at a time.
</details>

<details><summary><b>Step 2</b>: the loop</summary>

Most answers are `200`, but some are `000`, which means curl got **no answer at all**.

```text
200 200 000 200 200 200 000 000 200 200 …
```

7 of 124 requests got no answer.
</details>

<details><summary><b>Step 3</b>: Kubernetes is happy</summary>

```text
$ kubectl rollout status deployment/frontend
deployment "frontend" successfully rolled out
```

And every **new** pod was Ready before it received traffic.
</details>

> **Your call:** the new pods were ready. So where did those 7 requests go?

<details><summary><b>Hint</b></summary>

Look at the **old** pods, not the new ones. When an old pod is told to stop, how quickly does the load
balancer find out?
</details>

<details><summary><b>The answer</b></summary>

- **Root cause:** an old pod stopped **immediately** when Kubernetes told it to. Google's load balancer
  kept sending it visitors for a few more seconds, and they got no answer.
- **Fix:** a **`preStop` pause** of 15 seconds. The pod waits, the load balancer stops sending it
  traffic, and only then does the app exit. Result: **520 of 520** requests OK.
- **DevOps practice: zero-downtime deployment.** It doesn't come for free. **Drain before you stop.**
- **In our course:** [Kubernetes Stage 8](../kubernetes/stages/stage-8-rolling-updates.md) and the
  `preStop` lines in `kubernetes/manifests/02` and `06`.
- **Show it (if your cluster still runs):** remove the `preStop` lines, apply, run Stage 8's loop during
  an update, and watch the `000`s come back.
</details>

---

## Incident 2: $460 million in 45 minutes

*Knight Capital, a US stock-trading firm, 1 August 2012. Source: the US SEC order.*

**The setting.** Knight's software sends buy and sell orders to the stock market. A new version must run
on all **8 production servers** before the market opens on 1 August.

<details><summary><b>Step 1</b>: the deploy</summary>

Between 27 and 31 July, an engineer copies the new version onto the 8 servers **by hand**. No second
person checks it, and nothing checks it automatically.
</details>

<details><summary><b>Step 2</b>: 08:01, before the market opens</summary>

The system sends **97 automatic error e-mails** to the team. Nobody treats them as an alarm.
</details>

<details><summary><b>Step 3</b>: 09:30, the market opens</summary>

**One** of the 8 servers starts sending **millions of orders nobody asked for**. The other 7 behave
normally.
</details>

<details><summary><b>Step 4</b>: the rollback</summary>

Nobody understands why. The team **rolls back** the new code on the servers… and now **all 8** go wild.
</details>

<details><summary><b>Step 5</b>: 45 minutes later</summary>

Finally stopped. About 4 million trades, more than **$460 million lost**. The company nearly went bankrupt
and was sold months later.
</details>

> **Your call:** 8 servers, and only one went wild. What was different about it? And why did the rollback
> make the other 7 go wild too?

<details><summary><b>Hint</b></summary>

Did the manual copy really reach all 8? And the new version **reused an old setting (a flag)**: what did
that flag do in the old code?
</details>

<details><summary><b>The answer</b></summary>

- **Root cause:** the manual copy **missed 1 of the 8 servers**. The new version reused an old flag that,
  in the old code, switched on a test feature that had been dead for years. On the forgotten server, the
  old code was still there, and it woke up. The rollback put the old code back on the other 7, **but the
  flag stayed on**, so they woke up too.
- **Fix:** none in time. There was no check that every server ran the same version, nobody acted on the
  97 e-mails, and there was no quick kill switch.
- **DevOps practice: automated, identical deployments.** One build, deployed by a machine to every
  server, then **verified**. Alerts that someone actually reads. Delete dead code; never reuse a flag.
- **In our course:** the CI pipeline deploys the exact `sha-…` image it just built, and on Kubernetes
  every pod of a Deployment runs the same image. *But* our manual stages fall back to the `latest` tag:
  can you always say which version runs on our VM?
</details>

---

## Incident 3: One file, 8.5 million blue screens

*CrowdStrike, a security company, 19 July 2024.*

**The setting.** CrowdStrike's security agent runs on millions of Windows computers in companies around
the world. It receives small content updates many times a day, and every connected computer downloads them
within minutes.

<details><summary><b>Step 1</b>: 04:09 UTC</summary>

A routine content update goes out. An automatic checker had approved it.
</details>

<details><summary><b>Step 2</b>: minutes later</summary>

The computers that downloaded it crash with a blue screen. Airports, hospitals, banks and TV stations
stop.
</details>

<details><summary><b>Step 3</b>: 05:27 UTC</summary>

CrowdStrike pulls the update, **78 minutes** after sending it. Too late: about **8.5 million** Windows
machines already have it, and most of them crash again on every restart.
</details>

> **Your call:** the bad file was online for only 78 minutes, and it still broke 8.5 million machines. How
> should CrowdStrike have shipped it, so that a bad file breaks 1,000 machines instead?

<details><summary><b>Hint</b></summary>

Did every computer in the world need the update in the **same hour**? How do our rolling updates decide
whether to continue?
</details>

<details><summary><b>The answer</b></summary>

- **Root cause:** the checker itself had a bug, so the faulty file passed. Then it went to **every
  connected computer at once**: nothing tried it on a small group first.
- **Fix:** mostly by hand, one machine at a time: start in Safe Mode and delete the file (encrypted
  laptops each needed a recovery key). It took days. Afterwards, CrowdStrike started rolling out content
  updates in stages.
- **DevOps practice: roll out gradually.** First a few machines (a *canary*), then a few percent, then
  everyone. Watch health at every step, and **stop automatically** at the first sign of trouble.
- **In our course:** a rolling update replaces **one pod at a time** and continues only while new pods are
  ready, and `dev → test → main` stops bad code before production. Where would you add a canary?
</details>

---

## Incident 4: 300 GB gone in seconds

*GitLab.com, 31 January 2017.*

**The setting.** GitLab.com hosts code for millions of developers. Its data lives in a main database,
with a second copy (a *replica*) that follows it. The team has **five** backup methods.

<details><summary><b>Step 1</b>: evening</summary>

Spammers overload the database. The replica falls behind and stops copying.
</details>

<details><summary><b>Step 2</b>: late at night</summary>

A tired engineer decides to wipe the replica's data and copy it again from scratch. He has terminals open
to **both** servers.
</details>

<details><summary><b>Step 3</b>: the command</summary>

He runs the delete command in the wrong terminal: the **main** database. He notices within seconds, but
about 300 GB are already gone.
</details>

<details><summary><b>Step 4</b>: "no problem"</summary>

"We have five backup methods." The team starts checking them, one by one.
</details>

> **Your call:** vote. Of the five backup methods, how many gave them a usable backup? (0 to 5) Then: what
> would you change so that this can never happen again?

<details><summary><b>Hint</b></summary>

When had anyone last **restored** one of those backups?
</details>

<details><summary><b>The answer</b></summary>

- **Root cause:** a manual command, typed into production late at night, on the wrong server. And
  in GitLab's own words, of the five backup methods "none are working reliably or set up in the first
  place". The nightly database dump had been failing silently (a version mismatch, and the failure
  e-mails never arrived), the cloud disk snapshots were not switched on for the database, and nobody had
  ever tested a restore.
- **Fix:** luck. Disk snapshots normally ran only once a day, but an engineer had happened to take one by
  hand **6 hours** earlier, to test something. They restored from it and lost 6 hours of issues, comments
  and merge requests. They streamed the recovery live on YouTube and published everything.
- **DevOps practice: backups you have actually restored.** Test restores regularly and alert on backup
  failures. Make production obvious (a different prompt colour), and automate risky manual steps.
- **In our course:** [Stage 5](../stages/stage-5-ansible.md) backs up the database and **restores** it on
  a brand-new VM: exactly the part GitLab never tested.
</details>

---

## Incident 5: The Action nobody changed

*The GitHub Action tj-actions/changed-files, 14-15 March 2025.*

**The setting.** More than **23,000** GitHub repositories use the same small, popular Action in their CI
pipelines, written as `uses: tj-actions/changed-files@v45`. Those pipelines hold secrets: cloud keys,
Docker Hub tokens, deploy keys.

<details><summary><b>Step 1</b>: 14 March</summary>

Attackers get write access to the Action's repository and add their own code.
</details>

<details><summary><b>Step 2</b>: the tags</summary>

They **move** the existing version tags, like `v45`, to point to their new code.
</details>

<details><summary><b>Step 3</b>: the next pipeline runs</summary>

Every repository that runs a pipeline in the next day runs the attacker's code. **None of those teams
changed anything** in their own repository.
</details>

<details><summary><b>Step 4</b>: the logs</summary>

The code reads the secrets from the CI machine's memory and **prints them into the build log**. For public
repositories, anyone on the internet can read that log. Secrets leak from a few hundred of them.
</details>

> **Your call:** these teams changed nothing, so why did their pipelines run the attacker's code? What
> does `@v45` really point to?

<details><summary><b>Hint</b></summary>

A tag is a label on a commit. Who is allowed to move that label?
</details>

<details><summary><b>The answer</b></summary>

- **Root cause:** a version **tag can be moved** by whoever controls the repository. `@v45` meant
  "whatever the owner calls v45 today". The pipelines ran third-party code that could see all their
  secrets.
- **Fix:** the Action was cleaned up, and every affected team had to **rotate every secret** that might be
  in their logs.
- **DevOps practice: CI/CD supply-chain security.** Pin third-party code to something that can't move:
  a commit **SHA** for Actions (`uses: owner/action@<40-character SHA>`), a **digest** for images
  (`image@sha256:…`). Give each job only the secrets it needs. **Your pipeline is production:** protect it
  like production.
- **In our course:** we use tags everywhere: `actions/checkout@v7` in the workflows, `postgres:17.11-…`
  in Compose. Tags are friendly, but they can move. Should we pin them? What would it cost us?
- **Show it (10 seconds, in any git repo):** a tag really is just a movable label.

  ```console
  $ git tag v45 && git log -1 --format=%h v45
  $ git tag -f v45 HEAD~1 && git log -1 --format=%h v45     # same name, different code
  $ git tag -d v45
  ```
</details>

---

## Incident 6: A laptop, and $6.3 billion

*Binance, a cryptocurrency exchange, June to October 2026. Source: Binance's statement, as reported by
The Hacker News, 3 November 2026.*

**The setting.** Binance's wallet systems move customers' money. A team of wallet DevOps engineers runs
them.

<details><summary><b>Step 1</b>: June</summary>

A wallet DevOps engineer (call him A) searches online for a popular AI tool and installs it with a **fake
installer that contains malware**. Binance notices and changes his passwords and keys. But the attacker has
already learned who works on the wallet team.
</details>

<details><summary><b>Step 2</b>: September</summary>

A second engineer (B) is invited to a **job interview** on a job-hunting site. At the end, the
"interviewer" asks him to download a homework project onto his **work laptop**. The project contains
malware.
</details>

<details><summary><b>Step 3</b>: 20 October</summary>

From B's laptop, the attacker uses an internal company tool to take over the accounts of more engineers,
including A.
</details>

<details><summary><b>Step 4</b>: 29 October</summary>

On A's computer, the attacker finds a **token that can deploy containers into the wallet system**. They
deploy their own container. It talks to the internal service that signs payments, and sends money out
**outside the normal withdrawal checks**. Binance estimates the loss at about **$6.3 billion**.
</details>

> **Your call:** the attacker only ever controlled **laptops**. Why was a laptop enough to move billions?
> What would you change, so that it isn't?

<details><summary><b>Hint</b></summary>

Who should be able to deploy into the money system: a person's laptop, or the pipeline? And how long
should a deploy token live?
</details>

<details><summary><b>The answer</b></summary>

- **Root cause:** not one mistake, but several safety nets missing (Binance called it "not a single
  isolated breach"). The most DevOps one is that **a long-lived deploy token for production sat on a
  laptop**, so any malware on that laptop could deploy anything. Also, one deployed container could reach
  the payment-signing service, and untrusted software reached work machines twice.
- **Fix (Binance):** rebuilt the wallet system in a new environment, replaced the affected laptops,
  revoked the engineers' tokens and credentials, rebuilt access controls, and added monitoring for unusual
  behaviour. Investigators link the attack to North Korea's TraderTraitor group.
- **DevOps practice: least privilege and short-lived secrets.** Production deploys come from the
  **pipeline**, after review, not from a laptop. Tokens expire within minutes or hours, and they are kept
  in a secret store, not in files. A deployed container reaches only what it needs. Treat every developer
  laptop as a way in.
- **In our course, honestly:** our CI deploy key is `restrict`ed and the `deploy` user has no sudo. But
  in the Kubernetes lesson we deployed with `kubectl` **from our laptops with full admin rights**, and the
  Ansible vault password is a file on the laptop. **What could an attacker do with your laptop today?**
</details>

---

## Wrap-up: six incidents, six habits

| # | Incident | DevOps practice | The habit |
|:-:|---|---|---|
| 1 | Our dropped requests | zero-downtime deployment | Drain before you stop. |
| 2 | Knight Capital | automated, identical deployments | One build, deployed by a machine, verified on every server. |
| 3 | CrowdStrike | gradual rollout | Canary first; stop automatically at the first sign of trouble. |
| 4 | GitLab | backups | Test your restores, not just your backups. |
| 5 | tj-actions | supply-chain security | Pin third-party code; protect the pipeline like production. |
| 6 | Binance | least privilege | No production power on laptops: deploy from the pipeline, with short-lived tokens. |

None of these happened because of "bad engineers". They happened because **safety nets were missing**,
and that's what DevOps practices are: safety nets.

## Your turn (last 10 minutes)

> **Which of the six habits does our course project, or your own project, not have yet? What would it
> take to add it?**

Take 3 or 4 volunteers. Close with: pick **one** habit and add it before next week.
