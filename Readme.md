You must generate two ssh keys pairs, named `ansible_rsa` and `github_rsa`, located in `provision/files/master/.ssh/`. That is, you must create

```
provision/files/master/.ssh/ansible_rsa
provision/files/master/.ssh/ansible_rsa.pub

provision/files/master/.ssh/ansible_rsa
provision/files/master/.ssh/ansible_rsa.pub
```

with `ssh-keygen`.

Start the infrastructure with
