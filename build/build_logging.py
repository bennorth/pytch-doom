import colorlog

# Shared logging setup for the build scripts.  Messages go to stderr,
# so they stay out of mk_pytch_code's generated code on stdout.

colorlog.basicConfig(
    level="INFO",
    format="%(log_color)s%(levelname)s:%(name)s%(reset)s: %(message)s",
)


def get_logger(name):
    return colorlog.getLogger(name)
