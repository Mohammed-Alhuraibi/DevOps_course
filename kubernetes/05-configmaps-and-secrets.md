# 5. ConfigMaps and Secrets

[Lesson map](README.md) · [← 4. Services](04-services.md) · **5. ConfigMaps and Secrets** · [6. Storage and the backend →](06-storage-and-the-backend.md)

In the Docker stages the settings lived in `.env.prod` on the VM, next to the images, never inside
them. Kubernetes splits that file in two: a ConfigMap for the plain settings and a Secret for the
passwords. The images stay exactly the same.

**By the end:** the cluster holds the backend's settings and two random secrets, and you have seen
with your own eyes why a Secret is not a safe.

![ConfigMaps and Secrets: the .env.prod file of the Docker stages splits into the ConfigMap bugsquash-config with the plain settings NODE_ENV, COOKIE_SECURE, TRUST_PROXY, POSTGRES_DB, PGHOST, PGPORT, PGUSER and PGDATABASE, and the Secret bugsquash-secrets with POSTGRES_PASSWORD and JWT_SECRET; the unchanged backend image gets every ConfigMap key through envFrom, and PGPASSWORD and JWT_SECRET from the Secret, all as environment variables; a Secret is base64, not encryption: echo c2VjcmV0 | base64 -d prints secret](images/slides/k8s-06-configmaps-and-secrets.svg)

## 1. Apply the settings

Why: plain settings are safe to keep in Git, so they live in a file like everything else.

```console
laptop$ sed 's/ *#.*//' manifests/04-config.yaml | grep .
laptop$ kubectl apply -f manifests/04-config.yaml
laptop$ kubectl get configmap bugsquash-config
```

The first line shows the file without its comments and blank lines. You should see the settings,
then a ConfigMap with 10 entries:

```text
apiVersion: v1
kind: ConfigMap
metadata:
  name: bugsquash-config
data:
  NODE_ENV: production
  COOKIE_SECURE: "false"
  TRUST_PROXY: "2"
  AUTH_RATE_LIMIT_MAX: "500"
  POSTGRES_DB: bugsquash
  POSTGRES_USER: bugsquash
  PGHOST: postgres
  PGPORT: "5432"
  PGDATABASE: bugsquash
  PGUSER: bugsquash
configmap/bugsquash-config created
NAME               DATA   AGE
bugsquash-config   10     1s
```

Four of them come back later: `PGHOST: postgres` is the name of the database's Service (page 6),
`TRUST_PROXY` and `AUTH_RATE_LIMIT_MAX` matter behind Google's load balancer (page 7), and
`COOKIE_SECURE` turns `"true"` once the site has HTTPS (page 10).

## 2. Create the Secret

Why: passwords must never be in Git, so you create the Secret with a command instead of a file,
from random values that nobody ever types or sees.

```console
laptop$ kubectl create secret generic bugsquash-secrets \
          --from-literal=POSTGRES_PASSWORD="$(openssl rand -hex 24)" \
          --from-literal=JWT_SECRET="$(openssl rand -hex 32)"
laptop$ kubectl get secret bugsquash-secrets
```

`openssl rand -hex 24` prints 48 random characters, and `$( )` pastes them into the command.

You should see two entries, and no values:

```text
secret/bugsquash-secrets created
NAME                TYPE     DATA   AGE
bugsquash-secrets   Opaque   2      1s
```

## 3. Read the "secret"

Why: to see that a Secret is disguised, not locked.

```console
laptop$ kubectl get secret bugsquash-secrets -o jsonpath='{.data.JWT_SECRET}'; echo
laptop$ kubectl get secret bugsquash-secrets -o jsonpath='{.data.JWT_SECRET}' | base64 -d; echo
```

You should see a scrambled-looking string, then the real secret in plain text (ours, shortened here;
never paste yours anywhere):

```text
MThkNm…(88 characters)…
18d6…(64 characters)…
```

> [!WARNING]
> **Base64 is not encryption.** It is like writing a password in mirror writing: it looks
> scrambled, but anyone can read it back with one command and no key. So: never put a Secret's
> values in Git, and give few people the right to read Secrets.

## 4. See how the backend will read them

Why: the next page starts the backend, and this is how it gets its settings without a new image.

```console
laptop$ grep -A6 'envFrom' manifests/06-backend.yaml
```

You should see:

```yaml
          envFrom:
            - configMapRef: { name: bugsquash-config }
          # ...and these two come from the Secret.
          env:
            - name: PGPASSWORD
              valueFrom: { secretKeyRef: { name: bugsquash-secrets, key: POSTGRES_PASSWORD } }
            - name: JWT_SECRET            # the same secret in every copy: a login on
```

`envFrom` turns every key of the ConfigMap into an environment variable. The Secret's
`POSTGRES_PASSWORD` reaches the backend as `PGPASSWORD`, the name the backend looks for: one value,
two names, one for Postgres and one for the backend.

> [!NOTE]
> **One image, many places.** The image is the machine; the ConfigMap is the settings sheet taped
> next to it. Dev, test and production run the same image with different sheets.

## Checkpoint

- The ConfigMap `bugsquash-config` has 10 entries; the Secret `bugsquash-secrets` has 2.
- Settings live outside the image, and the secrets live outside Git.
- Anyone who may read a Secret can decode it: base64 is not encryption.

Next: a database that keeps its data, and the backend that uses it. [6. Storage and the backend](06-storage-and-the-backend.md).

<details>
<summary>Going deeper</summary>

- **Who may read Secrets** is decided by Kubernetes RBAC (roles and role bindings). On GKE your
  Google account's IAM role (Owner, Editor, ...) decides it too.
- **Secrets in Git, safely:** tools such as Sealed Secrets or the External Secrets Operator (with
  Google Secret Manager) keep only an encrypted or a reference version in the repository.
- **Changing a setting later** does not restart the pods that already read it. Page 10 shows what to
  do about that.

</details>

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `secrets "bugsquash-secrets" already exists` | You created it before: keep it. Recreating it after Postgres has started breaks the login to the database (page 6, troubleshooting). |
| `base64: invalid input` | Keep the `-o jsonpath='{.data.JWT_SECRET}'` part: it picks one value. |
| `error: exactly one NAME is required, got 2` | The line breaks of the `create secret` command got lost: copy it again, `\` must be the last character of each line. |
