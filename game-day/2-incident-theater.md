# Part 2: Incident theater (about 60 minutes)

[Game day](README.md) · [← Part 1: Quick revision](1-quick-revision.md) · **Part 2: Incident theater**

Six true stories of things going wrong. Three happened to **us** while building this course, and three
made world news. You are the on-call engineer.

**How each round works:**

1. Read the timeline aloud, one step at a time.
2. Ask the question. The room diagnoses out loud: guess, argue, ask questions back.
3. Stuck after 30 seconds? Click **Hint**.
4. Click **What really happened**: the cause, the fix and the lesson.

> [!TIP]
> Split the room into two teams (left and right) and keep score on the board: one point for the right
> cause, one for a good fix. No googling.

---

## Incident 1: It works once, fails in a loop

*Happened to your instructor, last week.*

1. **14:05.** Live demo in two hours. One request to the site answers **200**. Perfect.
2. **14:06.** The same request in a loop, for the demo, prints **`404 000 000`**, again and again.
3. **14:07.** Same URL, same laptop, same minute. One command works; the loop fails.

```text
❯ curl -s -o /dev/null -w "%{http_code}" http://$IP/
200
❯ while true; do curl -s -o /dev/null -w "%{http_code} " http://$IP/\; sleep 2; done
404 000 000 404 000 000 404 000 000 404 ^C
```

> **Your call:** why does the loop fail? Look very closely at what was typed.

<details><summary><b>Hint</b></summary>

Every round prints **three** codes, and the loop races: it never waits. Count the words after `curl`.
</details>

<details><summary><b>What really happened</b></summary>

- **Cause:** the shell (zsh's *url-quote-magic*) silently added a **`\`** before the **`;`**. So the
  semicolon no longer ended the command, and curl received three addresses: `/;` (404), `sleep` (000)
  and `2` (000). The `sleep` never ran.
- **Fix:** put the URL in quotes, `"http://$IP/"`. The shell leaves it alone, and the loop prints
  `200 200 200`.
- **Lesson:** when the result makes no sense, compare what you **think** you ran with what **really** ran.
- **In our course:** every URL in the Kubernetes docs is now quoted, and
  [Stage 8](../kubernetes/stages/stage-8-rolling-updates.md) lists this exact symptom.

*Ask the room:* who has copied a command from a web page and seen it behave differently? (Smart quotes,
invisible characters, line breaks.)
</details>

---

## Incident 2: The update that dropped requests

*Happened while building the Kubernetes lesson.*

1. We update the game from v1 to v2 on Kubernetes, one pod at a time.
2. A loop calls the site twice a second during the update.
3. Most answers are 200, but **7 of 124** get no answer at all (`000`).
4. Kubernetes reports: *rollout successful*. Every new pod was Ready.

```text
$ kubectl set image deployment/frontend frontend=alhuraibisaeed/bugsquash-frontend:sha-dcb0790
loop: 200 200 000 200 200 200 000 000 200 200 …
$ kubectl rollout status deployment/frontend
deployment "frontend" successfully rolled out
```

> **Your call:** every pod was "ready". So who sent visitors to a pod that was already gone?

<details><summary><b>Hint</b></summary>

Who stands between the visitors and the pods? How quickly does it learn that a pod is stopping?
</details>

<details><summary><b>What really happened</b></summary>

- **Cause:** an old pod stopped **immediately** when Kubernetes told it to. Google's load balancer kept
  sending it visitors for a few more seconds.
- **Fix:** a **`preStop` pause** of 15 seconds. The pod waits, the load balancer stops sending it
  visitors, and only then does the app shut down. Result: **520 of 520** requests OK.
- **Lesson:** zero downtime is designed, not free. **Drain before you stop.**
- **In our course:** [Stage 8](../kubernetes/stages/stage-8-rolling-updates.md) and the `preStop` lines in
  `kubernetes/manifests/02` and `06`.

*Ask the room:* where else must you drain first? (Server maintenance, database failover, scaling down.)
</details>

---

## Incident 3: HTTPS that would have taken the site down

*Caught while building the Kubernetes lesson, minutes before it reached visitors.*

1. **Goal:** the padlock on `k8s.gulfheight.com`. One file does two things: requests the certificate
   and sends every `http://` visitor to `https://`.
2. `kubectl apply`: all green. The certificate says **Provisioning** (that takes 15 to 60 minutes).
3. Meanwhile, every visitor on `http://` is redirected to `https://`…
4. …where there is no certificate yet. The browser shows an error page.

```text
$ kubectl apply -f https.yaml
managedcertificate created, redirect created
$ kubectl get managedcertificate
bugsquash-cert   Provisioning
$ curl -I http://k8s.gulfheight.com/
HTTP/1.1 301 Moved Permanently  →  https://k8s.gulfheight.com/
```

> **Your call:** what went wrong, and how would you roll this out instead?

<details><summary><b>Hint</b></summary>

Both steps were right. Look at the **order**, and at what "Provisioning" means.
</details>

<details><summary><b>What really happened</b></summary>

- **Cause:** the redirect was switched on **before** the certificate existed. Traffic moved to a door
  that was still locked.
- **Fix:** two steps. First request the certificate, while the site keeps working on HTTP. Only when it
  says **Active**, switch on the redirect.
- **Lesson:** before you send traffic somewhere, **check that it is ready.**
- **In our course:** `kubernetes/manifests/08-https.yaml` and `09-https-redirect.yaml` are now separate,
  and [Stage 10](../kubernetes/stages/stage-10-https-and-wrap-up.md) waits for *Active*.

*Ask the room:* it's the same idea as a readiness probe. Which other changes need a "ready?" check
before the switch? (DNS changes, database migrations, new versions.)
</details>

---

## Incident 4: $440 million in 45 minutes

*Knight Capital, 1 August 2012. Source: the US SEC report.*

1. **The night before.** New trading software is installed by hand on **8 servers**.
2. **09:30.** The stock market opens. Within minutes come millions of orders nobody asked for.
3. **09:45.** Nobody knows why. The team rolls back the new code… and it gets **worse**.
4. **10:15.** Finally stopped: about 4 million trades and **$440 million lost**. The company nearly goes
   bankrupt and is sold months later.

> **Your call:** what would you look for? And how can a rollback make things worse?

<details><summary><b>Hint</b></summary>

Were all 8 servers really the same? And besides the code, what else was changed?
</details>

<details><summary><b>What really happened</b></summary>

- **Cause:** the manual install **missed 1 of the 8 servers**. The new software reused an old setting
  (a flag), which woke up old, dead code on that forgotten server. The rollback removed the new code
  from the other 7, but the setting stayed on, so they ran the old code too.
- **Fix:** there was no quick, safe kill switch, and no check that all servers ran the same version.
- **Lesson:** **the same deploy, on every server, automated.** Delete dead code; never reuse a setting
  for something new.
- **In our course:** CI builds **one** image, and every copy runs exactly that image (`sha-…` tags) in
  dev, test and main.

*Ask the room:* why do we tag images with the git commit? (So we always know exactly what runs where.
Knight didn't.)
</details>

---

## Incident 5: `rm -rf` on the wrong server

*GitLab.com, 31 January 2017.*

1. **Late evening.** Spammers overload the database, and the backup copy (the *replica*) falls behind.
2. A tired engineer decides to wipe the replica's data folder and start it again.
3. He runs the delete… in the terminal of the **main** database, not the replica. He stops it after a
   second or two.
4. About 300 GB are gone. "No problem: we have **five** backup methods."

```text
db1$ # meant for the replica (db2)...
db1$ sudo rm -rf <database folder>
^C
```

> **Your call:** five backup methods. How many of them do you think worked? (Vote: 0 to 5.)

<details><summary><b>Hint</b></summary>

When had anyone last **restored** one of those backups?
</details>

<details><summary><b>What really happened</b></summary>

- **Cause:** none of the five methods gave a usable recent backup. Some had been **failing silently**
  for a long time (wrong versions, alert e-mails that never arrived), and nobody had tried a restore.
- **Fix:** they found a copy made for testing **6 hours** earlier. Six hours of issues, comments and
  merge requests were lost. They streamed the whole recovery live on YouTube.
- **Lesson:** a backup you have never restored is a **hope**, not a backup.
- **In our course:** Stage 5 (Ansible) backs up the database and the certificate, and restores them on a
  new VM. See [Stage 5](../stages/stage-5-ansible.md).

*Ask the room:* how would you avoid typing into the wrong server? (A different prompt colour for
production, read-only access by default, automation instead of manual commands.) And: when did you
last restore a backup of anything you own?
</details>

---

## Incident 6: One file, 8.5 million blue screens

*CrowdStrike, 19 July 2024.*

1. **Morning.** A security company sends a small configuration update to its agent on Windows PCs.
2. **Minutes later.** Blue screens: airports, hospitals, banks, TV stations.
3. **Reboot.** Blue screen again. The PCs can't start, so they can't download a fix.
4. **In total:** about **8.5 million** Windows machines, all at the same time.

> **Your call:** two questions. How do you fix machines that cannot even start? And how should the
> update have been shipped?

<details><summary><b>Hint</b></summary>

Did all 8.5 million need to get the update in the same minute?
</details>

<details><summary><b>What really happened</b></summary>

- **Cause:** a faulty content file passed a broken check and went to **every customer at once**. Nothing
  tested it on a small group first.
- **Fix:** by hand, machine by machine: start in Safe Mode and delete the file. Encrypted laptops also
  needed a recovery key each. It took days.
- **Lesson:** **roll out gradually.** First a few machines (a *canary*), then a few percent, then
  everyone, and stop at the first sign of trouble.
- **In our course:** `dev → test → main`, and rolling updates that replace one pod at a time.

*Ask the room:* where would you put a canary step in our pipeline?
</details>

---

## Wrap-up: six incidents, six habits

| Incident | Habit |
|---|---|
| 1. The zsh loop | Compare what you think you ran with what really ran. |
| 2. Dropped requests | Drain before you stop. |
| 3. HTTPS in the wrong order | Check it is ready before you send traffic. |
| 4. Knight Capital | The same deploy on every server, automated. |
| 5. GitLab | Test your restores, not just your backups. |
| 6. CrowdStrike | Roll out gradually. |

None of these were caused by "bad people". They were caused by **missing safety nets**, and that's
what DevOps practices are: safety nets.

## Your turn (last 10 minutes)

> **What's the worst bug you have ever caused, or almost caused? Which of today's six habits would have
> saved you?**

Start with your own story to break the ice, then take 3 or 4 volunteers.
