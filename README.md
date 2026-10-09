# Lupa Digital — Orange Pi 3 LTS

Visualizador leve de webcam com zoom digital progressivo de 1× até 8× controlado por push button, otimizado para Linux ARM com ambiente gráfico X11.

## Configuração para o hardware testado

- Câmera: **`/dev/video1`** (padrão; alterável por `--camera`)
- Captura preferencial: **1280×720 / 30 FPS / MJPEG**, com fallback para YUYV e 640×480 se necessário
- Botão de 4 pernas: **pino físico 21** (sinal, PH6) e **pino físico 6** (GND)
- Controlador GPIO: **`/dev/gpiochip1`**, linha **`230`** (offset `libgpiod`, **não** `wPi` 12)
- Pull-up no GPIO: solicitado pelo programa; se o driver não oferecer, instale resistor de 10 kΩ entre o sinal e **3,3 V**. Nunca aplique 5 V em um GPIO.

Conecte o botão entre o sinal e GND, sem alimentação externa. Para botões de quatro pernas, escolha pernas que só se conectem ao pressionar (a orientação pode variar).

## Instalação no Orange Pi

```bash
git clone https://github.com/LabSisData/lupa-digital.git
cd lupa-digital
chmod +x install_orangepi.sh
./install_orangepi.sh
```

O script instala OpenCV, NumPy, libgpiod e ferramentas V4L2, configura acesso aos GPIOs pelo grupo `gpio` e adiciona o usuário ao grupo `video`. **Saia da sessão e entre novamente, ou reinicie**, para os grupos terem efeito.

## Executar

```bash
cd ~/lupa-digital
python3 main.py
```

- **Botão físico:** cada clique avança **1× → 2× → 3× → 4× → 5× → 6× → 7× → 8× → 1×** (e repete).
- **Espaço:** executa a mesma sequência do botão, para teste pelo teclado.
- **Limite personalizável:** `--max-zoom 8` ou `ZOOM_MAX=8` no ambiente.
- **Esc / Q:** encerra o programa.
- **Tela cheia:** comportamento padrão. Passe `--windowed` para janela menor.

Para testar apenas a câmera:

```bash
python3 main.py --no-gpio --windowed
```

Para selecionar manualmente uma câmera ou ajustar desempenho:

```bash
python3 main.py --camera /dev/video1 --width 1280 --height 720 --fps 20
python3 main.py --camera /dev/video1 --width 640 --height 480 --fps 15 --windowed
python3 main.py --gpio-chip /dev/gpiochip1 --gpio-line 230
python3 main.py --max-zoom 8
```

## Diagnóstico

**A tela não mostra vídeo:** espere alguns segundos. Em vez de ficar branca, a nova versão mostra uma mensagem enquanto procura um formato suportado. Use `v4l2-ctl --list-devices` e `v4l2-ctl --list-formats-ext -d /dev/video1` para conferir a webcam. Feche outros aplicativos que possam estar usando a câmera. Se só funcionar em 640×480, ela talvez não suporte 720p no formato selecionado.

**Botão não funciona:** primeiro teste o circuito sem o aplicativo:

```bash
sudo gpio mode 12 in
sudo gpio mode 12 up
while true; do gpio read 12; sleep 0.2; done
```

O sinal deve ser `1` quando solto e `0` quando pressionado. Pressione `Ctrl+C` para parar. No código Python, use **chip1 / linha 230**, não `wPi 12`. Para conferir:

```bash
sudo gpioinfo gpiochip1 | grep -E 'line +230:'
ls -l /dev/gpiochip*
groups
```

Se o GPIO estiver indisponível (por exemplo, por permissões), a aplicação mantém a câmera funcionando e permite alternar o zoom por **Espaço**.

**Vídeo lento:** o programa captura em uma thread separada e exibe sempre o quadro mais recente. Experimente `--fps 15` ou `--width 640 --height 480` se a CPU estiver sobrecarregada. O desempenho final depende da webcam, do driver e do ambiente gráfico.

## Testes (não exigem hardware)

```bash
python3 -m unittest discover -s tests -v
```

## Estrutura

- `main.py` — interface em tela cheia, zoom progressivo de 1× a 8× e teclado
- `camera_stream.py` — captura em segundo plano e recuperação da câmera
- `gpio_button.py` — leitura do botão `libgpiod` 1.x/2.x com debounce
- `config.py` — valores padrão personalizáveis via variáveis de ambiente
- `install_orangepi.sh` — dependências e permissões
- `tests/test_logic.py` — testes automatizados da lógica
