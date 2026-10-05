# Orange Pi Camera Zoom

Projeto mínimo para o Orange Pi 3 LTS:

- câmera USB em 1280×720;
- janela em tela cheia;
- um botão físico alterna entre imagem normal (1×) e zoom central (2×);
- tecla `Espaço` também alterna o zoom durante os testes;
- tecla `Esc` ou `Q` fecha o programa.

## Hardware

- Orange Pi 3 LTS;
- sistema Linux com ambiente gráfico X11;
- câmera USB/UVC que suporte 1280×720;
- botão momentâneo normalmente aberto;
- fios para um GPIO e GND.

O botão deve ficar entre o GPIO escolhido e o GND. O programa usa pull-up interno quando o `libgpiod` 2.x estiver disponível. Se o sistema não oferecer pull-up interno, use um resistor de aproximadamente 10 kΩ entre o GPIO e 3,3 V.

**Nunca aplique 5 V em um GPIO do Orange Pi.**

## Requisitos no Orange Pi

O instalador usa os pacotes do sistema, pois eles funcionam melhor na arquitetura ARM do Orange Pi:

```bash
sudo apt update
sudo apt install -y python3 python3-opencv python3-libgpiod gpiod v4l-utils
sudo usermod -aG video "$USER"
```

Depois, encerre a sessão e entre novamente para o grupo `video` ser aplicado.

Em sistemas que ainda usam libgpiod 1.x, o pacote pode ter outro nome. Tente:

```bash
apt search python3-libgpiod
```

O programa possui compatibilidade com as APIs 1.x e 2.x do libgpiod.

Confira a câmera:

```bash
v4l2-ctl --list-devices
v4l2-ctl --list-formats-ext -d /dev/video0
```

Confira os GPIOs disponíveis:

```bash
gpioinfo
```

O projeto usa `/dev/gpiochip0` e linha `6` por padrão apenas como exemplo. Altere a linha para a que corresponde ao seu pino físico. O número mostrado por `gpioinfo` é um **offset lógico**, e não necessariamente o número escrito no conector físico da placa.

## Instalação

Na pasta do projeto:

```bash
chmod +x install_orangepi.sh
./install_orangepi.sh
```

## Configuração e execução

Exemplo usando a câmera `/dev/video0`, o chip padrão e a linha GPIO 6:

```bash
python3 main.py --camera /dev/video0 --gpio-chip /dev/gpiochip0 --gpio-line 6
```

Se quiser testar somente a câmera sem botão:

```bash
python3 main.py --camera /dev/video0 --no-gpio
```

Se a câmera estiver em outro dispositivo:

```bash
python3 main.py --camera /dev/video2 --gpio-line 6
```

Também é possível configurar por variáveis de ambiente:

```bash
export CAMERA_DEVICE=/dev/video0
export GPIO_CHIP=/dev/gpiochip0
export GPIO_LINE=6
export ZOOM_FACTOR=2.0
python3 main.py
```

## Teste rápido do botão

Antes de executar o programa, confira se o GPIO muda ao pressionar o botão:

```bash
gpiomon --num-events 5 /dev/gpiochip0 6
```

Se o comando não detectar nada, o número usado é provavelmente o offset lógico incorreto ou o botão está ligado em outro pino.

## Observações de desempenho

O projeto mantém o buffer da câmera pequeno para evitar atraso, solicita MJPEG quando a câmera oferece esse formato e faz o corte do zoom antes de redimensionar para a tela. O zoom é digital: ele amplia a região central da imagem, não altera a lente.

## Arquivos

- `main.py`: captura, tela cheia, zoom e controle do botão.
- `gpio_button.py`: leitura do botão usando libgpiod 1.x ou 2.x.
- `config.py`: valores padrão e variáveis de ambiente.
- `install_orangepi.sh`: instalação dos requisitos do Orange Pi.
- `requirements.txt`: dependências para teste com pip em computador Linux.
- `requirements-orange-pi.txt`: lista dos pacotes recomendados do sistema.
