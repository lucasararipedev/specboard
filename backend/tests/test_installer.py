import stat
import subprocess


def run_installer(client, tmp_path, *, with_extension: bool):
    script = client.get("/install/claude-code.sh")
    assert script.status_code == 200
    path = tmp_path / "install.sh"
    path.write_text(script.text)
    home = tmp_path / "home"
    if with_extension:
        # Só a extensão do VS Code: o Claude Code fica fora do PATH, dentro dela.
        bin_dir = home / ".vscode-server/extensions/anthropic.claude-code-2.1.0-linux-x64/resources/native-binary"
        bin_dir.mkdir(parents=True)
        fake = bin_dir / "claude"
        fake.write_text('#!/bin/sh\necho "claude chamado com: $*"\n')
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    else:
        home.mkdir()
    env = {"HOME": str(home), "PATH": "/usr/bin:/bin"}
    return subprocess.run(["sh", str(path)], capture_output=True, text=True, env=env)


def test_installer_finds_claude_inside_the_vscode_extension(client, tmp_path):
    result = run_installer(client, tmp_path, with_extension=True)
    assert result.returncode == 0, result.stderr
    assert "claude chamado com: plugin install specboard --marketplace lucasararipedev/specboard" in result.stdout
    assert "Pronto." in result.stdout


def test_installer_explains_when_claude_code_is_missing(client, tmp_path):
    result = run_installer(client, tmp_path, with_extension=False)
    assert result.returncode == 1
    assert "Não achei o Claude Code" in result.stderr
    assert "Claude Code: Install Plugin" in result.stderr


def test_installer_hints_custom_url_and_never_leaks_token(make_client):
    client = make_client(public_url="http://192.168.0.10:9000", api_token="segredo", allowed_hosts=("localhost",))
    text = client.get("/install/claude-code.sh").text
    assert "curl -fsSL http://192.168.0.10:9000/install/claude-code.sh | sh" in text
    assert "SPECBOARD_URL=http://192.168.0.10:9000" in text
    assert "segredo" not in text


def test_windows_installer_is_served(client):
    res = client.get("/install/claude-code.ps1")
    assert res.status_code == 200
    assert "irm http://localhost:8787/install/claude-code.ps1 | iex" in res.text
    assert "plugin install specboard --marketplace $marketplace" in res.text
