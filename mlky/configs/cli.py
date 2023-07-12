import click

from . import generate


@click.command(name="generate")
@click.option('-f', '--file',
    help         = 'File to write the generated YAML to.',
    required     = True
)
@click.option('-d', '--defs',
    help         = 'Definitions file to generate from.',
    required     = True,
    default      = '',
    show_default = True
)
@click.option('-s', '--style',
    help         = 'Style to generate the output as.',
    type         = click.Choice(['full'], case_sensitive=False),
    default      = 'full',
    show_default = True
)
@click.option('-c', '--comments',
    help         = 'Style to write the comments for each option.',
    type         = click.Choice(['inline', 'coupled', 'none'], case_sensitive=False),
    default      = 'inline',
    show_default = True
)
def click_generate(defs, file, style, comments):
    """
    """
    lines = generate(
        defs     = defs,
        file     = file,
        style    = style,
        comments = comments
    )
    string = '\n'.join(lines)
    click.echo(f'Generate template(style={style}, comments={comments}) to {file}')


@click.command(name="validate")
@click.option('-f', '--file',
    help         = 'File to validate.',
    required     = True
)
@click.option('-i', '--inherit',
    help         = 'Inheritance to use for the input config.',
)
@click.option('-d', '--defs',
    help         = 'Definitions file for validation.',
    required     = True,
    default      = '',
    show_default = True
)
@click.option('-di', '--defs_inherit',
    help         = 'Inheritance to use for the definitions file.',
)
def click_validate(file, inherit, defs, defs_inherit):
    """
    """
    click.echo(f'Validation results for {file}:')
    config = Config(file, inherit, defs, defs_inherit, _validate=False)
    errors = config.validate_(_raise=False)
    if not errors:
        click.echo(f'No errors were found.')
