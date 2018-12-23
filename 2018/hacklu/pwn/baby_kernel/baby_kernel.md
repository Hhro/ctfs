## Knowledge

### 1. cred 구조체

```c
struct cred init_cred = {
	.usage			= ATOMIC_INIT(4),
#ifdef CONFIG_DEBUG_CREDENTIALS
	.subscribers		= ATOMIC_INIT(2),
	.magic			= CRED_MAGIC,
#endif
	.uid			= GLOBAL_ROOT_UID,
	.gid			= GLOBAL_ROOT_GID,
	.suid		struct cred {
	atomic_t	usage;
#ifdef CONFIG_DEBUG_CREDENTIALS
	atomic_t	subscribers;	/* number of processes subscribed */
	void		*put_addr;
	unsigned	magic;
#define CRED_MAGIC	0x43736564
#define CRED_MAGIC_DEAD	0x44656144
#endif
	kuid_t		uid;		/* real UID of the task */
	kgid_t		gid;		/* real GID of the task */
	kuid_t		suid;		/* saved UID of the task */
	kgid_t		sgid;		/* saved GID of the task */
	kuid_t		euid;		/* effective UID of the task */
	kgid_t		egid;		/* effective GID of the task */
	kuid_t		fsuid;		/* UID for VFS ops */
	kgid_t		fsgid;		/* GID for VFS ops */
	unsigned	securebits;	/* SUID-less security management */
	kernel_cap_t	cap_inheritable; /* caps our children can inherit */
	kernel_cap_t	cap_permitted;	/* caps we're permitted */
	kernel_cap_t	cap_effective;	/* caps we can actually use */
	kernel_cap_t	cap_bset;	/* capability bounding set */
#ifdef CONFIG_KEYS
	unsigned char	jit_keyring;	/* default keyring to attach requested
					 * keys to */
	struct key __rcu *session_keyring; /* keyring inherited over fork */
	struct key	*process_keyring; /* keyring private to this process */
	struct key	*thread_keyring; /* keyring private to this thread */
	struct key	*request_key_auth; /* assumed request_key authority */
#endif
#ifdef CONFIG_SECURITY
	void		*security;	/* subjective LSM security */
#endif
	struct user_struct *user;	/* real user ID subscription */
	struct user_namespace *user_ns; /* user_ns the caps and keyrings are relative to. */
	struct group_info *group_info;	/* supplementary groups for euid/fsgid */
	struct rcu_head	rcu;		/* RCU deletion hook */
};	= GLOBAL_ROOT_UID,
	.sgid			= GLOBAL_ROOT_GID,
	.euid			= GLOBAL_ROOT_UID,
	.egid			= GLOBAL_ROOT_GID,
	.fsuid			= GLOBAL_ROOT_UID,
	.fsgid			= GLOBAL_ROOT_GID,
	.securebits		= SECUREBITS_DEFAULT,
	.cap_inheritable	= CAP_EMPTY_SET,
	.cap_permitted		= CAP_FULL_SET,
	.cap_effective		= CAP_FULL_SET,
	.cap_bset		= CAP_FULL_SET,
	.user			= INIT_USER,
	.user_ns		= &init_user_ns,
	.group_info		= &init_groups,
};
```

- Credential Structure : 실행중인 프로세스의 권한정보를 담고 있는 구조체


### 2. prepare_kernel_cred

```c
struct cred *prepare_kernel_cred(struct task_struct *daemon)
{
	const struct cred *old;
	struct cred *new;

	new = kmem_cache_alloc(cred_jar, GFP_KERNEL);
	if (!new)
		return NULL;

	kdebug("prepare_kernel_cred() alloc %p", new);

	if (daemon)
		old = get_task_cred(daemon);
	else
		old = get_cred(&init_cred);

	validate_creds(old);

	*new = *old;
	atomic_set(&new->usage, 1);
	set_cred_subscribers(new, 0);
	get_uid(new->user);
	get_user_ns(new->user_ns);
	get_group_info(new->group_info);

#ifdef CONFIG_KEYS
	new->session_keyring = NULL;
	new->process_keyring = NULL;
	new->thread_keyring = NULL;
	new->request_key_auth = NULL;
	new->jit_keyring = KEY_REQKEY_DEFL_THREAD_KEYRING;
#endif

#ifdef CONFIG_SECURITY
	new->security = NULL;
#endif
	if (security_prepare_creds(new, old, GFP_KERNEL) < 0)
		goto error;

	put_cred(old);
	validate_creds(new);
	return new;

error:
	put_cred(new);
	put_cred(old);
	return NULL;
}
EXPORT_SYMBOL(prepare_kernel_cred);
```

12번 분기문에서 이 함수에 전달된 인자가 0이면 old = init_cred이 됨. 

```c
struct cred init_cred = {
	.usage			= ATOMIC_INIT(4),
#ifdef CONFIG_DEBUG_CREDENTIALS
	.subscribers		= ATOMIC_INIT(2),
	.magic			= CRED_MAGIC,
#endif
	.uid			= GLOBAL_ROOT_UID,
	.gid			= GLOBAL_ROOT_GID,
	.suid			= GLOBAL_ROOT_UID,
	.sgid			= GLOBAL_ROOT_GID,
	.euid			= GLOBAL_ROOT_UID,
	.egid			= GLOBAL_ROOT_GID,
	.fsuid			= GLOBAL_ROOT_UID,
	.fsgid			= GLOBAL_ROOT_GID,
	.securebits		= SECUREBITS_DEFAULT,
	.cap_inheritable	= CAP_EMPTY_SET,
	.cap_permitted		= CAP_FULL_SET,
	.cap_effective		= CAP_FULL_SET,
	.cap_bset		= CAP_FULL_SET,
	.user			= INIT_USER,
	.user_ns		= &init_user_ns,
	.group_info		= &init_groups,
};
```

init_cred의 uid, gid등의 모든 id는 root이므로, old는 root권한을 가진 cred structure가 됨. 그 뒤, old를 new에 옮기고, new를 반환함.

 `preparekernelcred(0)` 는 root권한의 cred structure를 반환함.

### 3.commit_creds

```c
int commit_creds(struct cred *new)
{
	struct task_struct *task = current;
	const struct cred *old = task->real_cred;

	BUG_ON(task->cred != old);
#ifdef CONFIG_DEBUG_CREDENTIALS
	BUG_ON(read_cred_subscribers(old) < 2);
	validate_creds(old);
	validate_creds(new);
#endif
	BUG_ON(atomic_read(&new->usage) < 1);

	get_cred(new); /* we will require a ref for the subj creds too */

	/* dumpability changes */
	if (!uid_eq(old->euid, new->euid) ||
	    !gid_eq(old->egid, new->egid) ||
	    !uid_eq(old->fsuid, new->fsuid) ||
	    !gid_eq(old->fsgid, new->fsgid) ||
	    !cred_cap_issubset(old, new)) {
		if (task->mm)
			set_dumpable(task->mm, suid_dumpable);
		task->pdeath_signal = 0;
		smp_wmb();
	}

	/* alter the thread keyring */
	if (!uid_eq(new->fsuid, old->fsuid))
		key_fsuid_changed(task);
	if (!gid_eq(new->fsgid, old->fsgid))
		key_fsgid_changed(task);

	/* do it
	 * RLIMIT_NPROC limits on user->processes have already been checked
	 * in set_user().
	 */
	alter_cred_subscribers(new, 2);
	if (new->user != old->user)
		atomic_inc(&new->user->processes);
	rcu_assign_pointer(task->real_cred, new);
	rcu_assign_pointer(task->cred, new);
	if (new->user != old->user)
		atomic_dec(&old->user->processes);
	alter_cred_subscribers(old, -2);

	/* send notifications */
	if (!uid_eq(new->uid,   old->uid)  ||
	    !uid_eq(new->euid,  old->euid) ||
	    !uid_eq(new->suid,  old->suid) ||
	    !uid_eq(new->fsuid, old->fsuid))
		proc_id_connector(task, PROC_EVENT_UID);

	if (!gid_eq(new->gid,   old->gid)  ||
	    !gid_eq(new->egid,  old->egid) ||
	    !gid_eq(new->sgid,  old->sgid) ||
	    !gid_eq(new->fsgid, old->fsgid))
		proc_id_connector(task, PROC_EVENT_GID);

	/* release the old obj and subj refs both */
	put_cred(old);
	put_cred(old);
	return 0;
}
EXPORT_SYMBOL(commit_creds);
```

현재 프로세스의 cred구조체를 인자로 전달받은 new cred구조체로 치환함.

따라서 `commit_creds(prepare_kernel_creds(0))`은 현재 프로세스의 권한을 root로 상승시킵니다.

---

## Analyze...

run.sh를 실행하면, 제공받은 파일들이 qemu에서 구동됩니다. 

```bash
#run.sh
qemu-system-x86_64 -monitor /dev/null -m 64 -nographic -kernel "bzImage" -initrd initrd.cpio -append "console=ttyS0 init='/init'"
```

run.sh를 읽어보면, 커널을 구동한뒤, /init를 실행하는 것을 알 수 있습니다.

init파일을 얻기 위해 제공된 initrd.cpio의 압축을 풀면

```bash
$hhro cpio -i <./initrd.cpio
$hhro ls
bin                 etc   home  initrd.cpio  root  var
client_kernel_baby  flag  init  lib          usr
```

위와 같은 파일들을 구할 수 있습니다.

init은 일종의 쉘 스크립트인데, 읽어보면

```bash
$hhro cat init
#!/bin/busybox sh
# /bin/sysinfo

/bin/busybox --install /bin
/bin/mkdir /sbin
/bin/busybox --install /sbin

export PATH="/bin;$PATH"
export LD_LIBRARY_PATH="/lib"

#for util in dropbear dbclient dropbearkey dropbearconvert; do
#	ln -s /bin/dropbearmulti /bin/$util
#done

mkdir -p /dev /sys /proc /tmp
mkdir -p /dev/pts

mount -t devtmpfs none /dev
# mount -t sysfs sys /sys
mount -t proc proc /proc
mount -t tmpfs none /tmp
mount -t devpts devpts /dev/pts

# chown
chown -R 0:0  /bin /etc /home /init /lib /root /tmp /var
chown -R 1000:1000 /home/user
chown 0:0 / /dev /proc /sys
chown 0:0 /flag

# chmod
chmod -R 700 /etc /home /root /var
chmod -R 755 /bin /init /lib
chmod -R 1777 /tmp
chmod 755 /
chmod 755 /etc
chmod 744 /etc/passwd /etc/group
chmod 755 /home
chmod 700 /etc/shadow

chmod 700 /flag

# echo 1 > /proc/sys/kernel/printk

mkdir -p /lib/modules/$(uname -r)

# Setup ip configuration
#ip link set lo up
#ip link set eth0 up
#udhcpc
#dropbear

insmod "/lib/modules/$(uname -r)/kernel_baby.ko"
chmod +rw /dev/flux_baby
chmod +x /client_kernel_baby

# sysinfo
# exec /bin/sh /dev/ttyS0>&0 1>/dev/ttyS0 2>&1
sleep 2

su user -c /client_kernel_baby

poweroff -f

#while true; do
#	/bin/setsid /bin/sh -c 'exec /bin/login </dev/ttyS0 >/dev/ttyS0 2>&1'
#done
```

다음을 알 수 있습니다.

- flag은 root소유이며, root에게만 rwx가 허용된다.
- kernel_baby.ko라는 모듈을 실행한다.
- user권한으로 client_kernel_baby를 실행한다.

따라서 상세한 분석을 위해, `client_kernel_baby`와 `kernel_baby.ko`모듈을 리버싱 해봐야 합니다. 결과적으로 보자면, 이 둘은 출제자의 설명 그대로 동작하므로 분석할 필요가 없습니다. ; )

---

## Exploit

사실 이 문제를 풀기위해 위와같은 정도의 분석은 필요하지 않습니다... 
Knowledge에 서술된 지식들이 이미 있다면, KASLR이 걸려있지 않기 때문에 vmlinux에서 두 함수의 주소들만 읽어내면 풀 수 있습니다.

1. prepare_kernel_creds : 0xFFFFFFFF8104EE50 (18446744071579168336)
2. commit_creds : 0xFFFFFFFF8104E9D0 (18446744071579167184)

call함수를 이용해서 commit_creds(prepare_kernel_creds(0))을 수행하고, read_file함수를 호출하여 flag를 읽으면 끝납니다. 

![prepare](/images/prepare.png)

![commit](/images/commit.png)

![solve](/images/flag.png)

---

## Review

- commit_creds(prepare_kernel_creds(0)) : 로컬 권한 상승
- 커널 함수는 vmlinux안에 정의되어 있음