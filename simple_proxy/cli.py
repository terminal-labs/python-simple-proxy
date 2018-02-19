import click
from tornado import ioloop

from simple_proxy.proxy import make_app

context_settings = {
    'help_option_names': ['-h', '--help'],
}

@click.command(context_settings=context_settings)
@click.option('-p', '--port', type=int, default=8000,
              help='The port to serve the proxy on. Defaults to 8000')
@click.option('-v', '--verbose', 'verbosity', count=True,
              help='Increases the verbosity of the logging.')
def cli(port, verbosity):
    click.echo('Ctrl + \ to kill.')
    app = make_app(verbosity)
    app.listen(port, address="0.0.0.0")
    ioloop.IOLoop.current().start()

if __name__ == "__main__":
    cli()

main = cli
