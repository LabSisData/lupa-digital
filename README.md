# Lupa Digital — Orange Pi 3 LTS

Visualizador leve de webcam com **zoom digital fixo de 3×**, otimizado para Linux ARM com ambiente gráfico X11.

O aplicativo abre a câmera e mantém a imagem sempre ampliada em **3×**. Não há botão físico, tecla ou parâmetro para alterar o nível de zoom.

## Configuração padrão

- Câmera: `/dev/video1` (alterável por `--camera`)
- Captura preferencial: **1280×720 / 30 FPS / MJPEG**
- Zoom: **3× fixo**
- Tela cheia por padrão

## Instalação no Orange Pi

```bash
git clone https://github.com/LabSisData/lupa-digital.git
cd lupa-digital
chmod +x install_orangepi.sh
./install_orangepi.sh
```

Depois da instalação, encerre a sessão e entre novamente ou reinicie para garantir acesso ao dispositivo de vídeo.

## Executar

```bash
cd ~/lupa-digital
python3 main.py
```

Controles:

- **Esc / Q:** encerra o programa.
- **Zoom:** sempre **3×**.
- **Tela cheia:** padrão. Use `--windowed` para abrir em uma janela.

Para testar em janela:

```bash
python3 main.py --windowed
```

Para selecionar manualmente uma câmera ou ajustar o desempenho:

```bash
python3 main.py --camera /dev/video1 --width 1280 --height 720 --fps 20
python3 main.py --camera /dev/video1 --width 640 --height 480 --fps 15 --windowed
```

## Diagnóstico

**A tela não mostra vídeo:** espere alguns segundos. O programa mostra uma mensagem enquanto procura um formato suportado. Use:

```bash
v4l2-ctl --list-devices
v4l2-ctl --list-formats-ext -d /dev/video1
```

Feche outros aplicativos que possam estar usando a câmera. Se necessário, tente 640×480 e 15 FPS.

**Vídeo lento:** experimente:

```bash
python3 main.py --width 640 --height 480 --fps 15
```

A captura é feita em uma thread separada e a interface exibe sempre o quadro mais recente.

## Testes

Os testes não exigem câmera física:

```bash
python3 -m unittest discover -s tests -v
```

## Estrutura

- `main.py` — interface em tela cheia e zoom fixo de 3×
- `camera_stream.py` — captura em segundo plano e recuperação da câmera
- `config.py` — valores padrão da câmera
- `install_orangepi.sh` — instalação das dependências
- `tests/test_logic.py` — testes automatizados
