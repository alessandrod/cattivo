#ifndef _XTABLES_H
#define _XTABLES_H

/*
 * Changing any structs/functions may incur a needed change
 * in libxtables_vcurrent/vage too.
 */

#include <sys/socket.h> /* PF_* */
#include <sys/types.h>
#include <limits.h>
#include <stdbool.h>
#include <netinet/in.h>
#include <net/if.h>
#include <linux/types.h>
#include <linux/netfilter.h>
#include <linux/netfilter/x_tables.h>

#ifndef IPPROTO_SCTP
#define IPPROTO_SCTP 132
#endif
#ifndef IPPROTO_DCCP
#define IPPROTO_DCCP 33
#endif
#ifndef IPPROTO_MH
#	define IPPROTO_MH 135
#endif
#ifndef IPPROTO_UDPLITE
#define IPPROTO_UDPLITE	136
#endif

#define XTABLES_VERSION "libxtables.so.@libxtables_vmajor@"
#define XTABLES_VERSION_CODE @libxtables_vmajor@

#ifndef NFPROTO_IPV4
#define NFPROTO_IPV4 2
#endif

#ifndef NFPROTO_IPV6
#define NFPROTO_IPV6 10
#endif

struct in_addr;

/* Include file for additions: new matches and targets. */
struct xtables_match
{
	struct xtables_match *next;

	const char *name;

	/* Revision of match (0 by default). */
	u_int8_t revision;

	u_int16_t family;

	const char *version;

	/* Size of match data. */
	size_t size;

	/* Size of match data relevent for userspace comparison purposes */
	size_t userspacesize;

	/* Function which prints out usage message. */
	void (*help)(void);

	/* Initialize the match. */
	void (*init)(struct xt_entry_match *m);

	/* Function which parses command options; returns true if it
           ate an option */
	/* entry is struct ipt_entry for example */
	int (*parse)(int c, char **argv, int invert, unsigned int *flags,
		     const void *entry,
		     struct xt_entry_match **match);

	/* Final check; exit if not ok. */
	void (*final_check)(unsigned int flags);

	/* Prints out the match iff non-NULL: put space at end */
	/* ip is struct ipt_ip * for example */
	void (*print)(const void *ip,
		      const struct xt_entry_match *match, int numeric);

	/* Saves the match info in parsable form to stdout. */
	/* ip is struct ipt_ip * for example */
	void (*save)(const void *ip, const struct xt_entry_match *match);

	/* Pointer to list of extra command-line options */
	const struct option *extra_opts;

	/* Ignore these men behind the curtain: */
	unsigned int option_offset;
	struct xt_entry_match *m;
	unsigned int mflags;
#ifdef NO_SHARED_LIBS
	unsigned int loaded; /* simulate loading so options are merged properly */
#endif
};

struct xtables_target
{
	struct xtables_target *next;

	const char *name;

	/* Revision of target (0 by default). */
	u_int8_t revision;

	u_int16_t family;

	const char *version;

	/* Size of target data. */
	size_t size;

	/* Size of target data relevent for userspace comparison purposes */
	size_t userspacesize;

	/* Function which prints out usage message. */
	void (*help)(void);

	/* Initialize the target. */
	void (*init)(struct xt_entry_target *t);

	/* Function which parses command options; returns true if it
           ate an option */
	/* entry is struct ipt_entry for example */
	int (*parse)(int c, char **argv, int invert, unsigned int *flags,
		     const void *entry,
		     struct xt_entry_target **targetinfo);

	/* Final check; exit if not ok. */
	void (*final_check)(unsigned int flags);

	/* Prints out the target iff non-NULL: put space at end */
	void (*print)(const void *ip,
		      const struct xt_entry_target *target, int numeric);

	/* Saves the targinfo in parsable form to stdout. */
	void (*save)(const void *ip,
		     const struct xt_entry_target *target);

	/* Pointer to list of extra command-line options */
	const struct option *extra_opts;

	/* Ignore these men behind the curtain: */
	unsigned int option_offset;
	struct xt_entry_target *t;
	unsigned int tflags;
	unsigned int used;
#ifdef NO_SHARED_LIBS
	unsigned int loaded; /* simulate loading so options are merged properly */
#endif
};

struct xtables_rule_match {
	struct xtables_rule_match *next;
	struct xtables_match *match;
	/* Multiple matches of the same type: the ones before
	   the current one are completed from parsing point of view */
	bool completed;
};

/**
 * struct xtables_pprot -
 *
 * A few hardcoded protocols for 'all' and in case the user has no
 * /etc/protocols.
 */
struct xtables_pprot {
	const char *name;
	u_int8_t num;
};

enum xtables_tryload {
	XTF_DONT_LOAD,
	XTF_DURING_LOAD,
	XTF_TRY_LOAD,
	XTF_LOAD_MUST_SUCCEED,
};

enum xtables_exittype {
	OTHER_PROBLEM = 1,
	PARAMETER_PROBLEM,
	VERSION_PROBLEM,
	RESOURCE_PROBLEM,
	XTF_ONLY_ONCE,
	XTF_NO_INVERT,
	XTF_BAD_VALUE,
	XTF_ONE_ACTION,
};

struct xtables_globals
{
	unsigned int option_offset;
	const char *program_name, *program_version;
	struct option *orig_opts;
	struct option *opts;
	void (*exit_err)(enum xtables_exittype status, const char *msg, ...) __attribute__((noreturn, format(printf,2,3)));
};

extern const char *xtables_modprobe_program;
extern struct xtables_match *xtables_matches;
extern struct xtables_target *xtables_targets;

extern void xtables_init(void);
extern void xtables_set_nfproto(uint8_t);
extern void *xtables_calloc(size_t, size_t);
extern void *xtables_malloc(size_t);

extern int xtables_insmod(const char *, const char *, bool);
extern int xtables_load_ko(const char *, bool);
extern int xtables_set_params(struct xtables_globals *xtp);
extern void xtables_set_revision(char *name, u_int8_t revision);
extern void xtables_free_opts(int reset_offset);
extern struct option *xtables_merge_options(struct option *oldopts,
	const struct option *newopts, unsigned int *option_offset);

extern int xtables_init_all(struct xtables_globals *xtp, uint8_t nfproto);
extern struct xtables_match *xtables_find_match(const char *name,
	enum xtables_tryload, struct xtables_rule_match **match);
extern struct xtables_target *xtables_find_target(const char *name,
	enum xtables_tryload);

/* Your shared library should call one of these. */
extern void xtables_register_match(struct xtables_match *me);
extern void xtables_register_target(struct xtables_target *me);

extern bool xtables_strtoul(const char *, char **, unsigned long *,
	unsigned long, unsigned long);
extern bool xtables_strtoui(const char *, char **, unsigned int *,
	unsigned int, unsigned int);
extern int xtables_service_to_port(const char *name, const char *proto);
extern u_int16_t xtables_parse_port(const char *port, const char *proto);
extern void
xtables_parse_interface(const char *arg, char *vianame, unsigned char *mask);

/* this is a special 64bit data type that is 8-byte aligned */
#define aligned_u64 u_int64_t __attribute__((aligned(8)))

int xtables_check_inverse(const char option[], int *invert,
	int *my_optind, int argc);
extern struct xtables_globals *xt_params;
#define xtables_error (xt_params->exit_err)

extern void xtables_param_act(unsigned int, const char *, ...);

extern const char *xtables_ipaddr_to_numeric(const struct in_addr *);
extern const char *xtables_ipaddr_to_anyname(const struct in_addr *);
extern const char *xtables_ipmask_to_numeric(const struct in_addr *);
extern struct in_addr *xtables_numeric_to_ipaddr(const char *);
extern struct in_addr *xtables_numeric_to_ipmask(const char *);
extern void xtables_ipparse_any(const char *, struct in_addr **,
	struct in_addr *, unsigned int *);

extern struct in6_addr *xtables_numeric_to_ip6addr(const char *);
extern const char *xtables_ip6addr_to_numeric(const struct in6_addr *);
extern const char *xtables_ip6addr_to_anyname(const struct in6_addr *);
extern const char *xtables_ip6mask_to_numeric(const struct in6_addr *);
extern void xtables_ip6parse_any(const char *, struct in6_addr **,
	struct in6_addr *, unsigned int *);

/**
 * Print the specified value to standard output, quoting dangerous
 * characters if required.
 */
extern void xtables_save_string(const char *value);

#ifdef NO_SHARED_LIBS
#	ifdef _INIT
#		undef _init
#		define _init _INIT
#	endif
	extern void init_extensions(void);
#else
#	define _init __attribute__((constructor)) _INIT
#endif

extern const struct xtables_pprot xtables_chain_protos[];
extern u_int16_t xtables_parse_protocol(const char *s);

#ifdef XTABLES_INTERNAL

/* Shipped modules rely on this... */

#	ifndef ARRAY_SIZE
#		define ARRAY_SIZE(x) (sizeof(x) / sizeof(*(x)))
#	endif

extern void _init(void);

#endif

#endif /* _XTABLES_H */
