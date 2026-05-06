# Sistema de Reconhecimento Automático de Placas Veiculares

Este projeto foi realizado como atividade avaliativa no primeiro ano de BCC. Implementa um sistema de reconhecimento automático de placas veiculares desenvolvido para rodar na nuvem. Desenvolvido em conjunto com um projeto complementar que captura imagens de vídeo através de uma webcam local e integra-se com este sistema para controle de acesso automatizado.

## Funcionalidades

- **Captura de Vídeo**: Captura frames de vídeo em tempo real de uma fonte de stream (atualmente configurado para Twitch, mas pode ser adaptado para webcam local).
- **Processamento de Imagem**: Utiliza OpenCV para detectar contornos e identificar regiões de interesse (ROIs) que correspondem a placas veiculares.
- **Reconhecimento Óptico de Caracteres (OCR)**: Emprega Tesseract OCR para extrair o texto das placas detectadas.
- **Verificação de Autorização**: Consulta um banco de dados MySQL para verificar se a placa detectada está autorizada para acesso.
- **Controle de Cancela**: Envia comandos seriais para um Arduino controlar a abertura/fechamento de uma cancela automática.
- **Logging**: Registra eventos de abertura de cancela com timestamp para auditoria.

## Tecnologias Utilizadas

- **Python 3.12**: Linguagem principal do projeto.
- **OpenCV**: Para processamento de imagens e detecção de contornos.
- **Tesseract OCR**: Para reconhecimento de texto em imagens.
- **Streamlink**: Para captura de streams de vídeo.
- **PyMySQL**: Para conexão e consultas ao banco de dados MySQL.
- **PySerial**: Para comunicação serial com Arduino.
- **Railway**: Plataforma de deploy na nuvem.

## Arquitetura e Boas Práticas

O código foi refatorado seguindo princípios de Programação Orientada a Objetos (POO) e boas práticas de desenvolvimento:

### Classes Principais

- **`Config`**: Gerencia todas as configurações da aplicação carregadas de variáveis de ambiente.
- **`Database`**: Encapsula a lógica de conexão e consultas ao banco de dados MySQL, com tratamento adequado de erros.
- **`ArduinoController`**: Responsável pela comunicação serial com o Arduino para controle da cancela.
- **`ImageProcessor`**: Centraliza todo o processamento de imagens, detecção de placas e OCR.
- **`ALPRApp`**: Classe principal que orquestra o fluxo da aplicação.

### Melhorias Implementadas

- **Segurança**: Credenciais do banco de dados movidas para variáveis de ambiente (arquivo `.env`).
- **Separação de Responsabilidades**: Cada classe tem uma responsabilidade específica.
- **Tratamento de Erros**: Uso de try-except com logging apropriado.
- **Logging Estruturado**: Substituição de prints por logging configurado.
- **Configuração Centralizada**: Todas as configurações gerenciadas pela classe `Config`.
- **Prevenção de SQL Injection**: Uso de parâmetros preparados nas consultas.
- **Gerenciamento de Recursos**: Conexões com banco e serial fechadas adequadamente.

## Configuração e Deploy

### Pré-requisitos

- Python 3.12
- Tesseract OCR instalado
- Acesso a banco de dados MySQL
- Arduino conectado (opcional para controle físico)

### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/callmedigo/nuvem.git
   cd nuvem
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure as variáveis de ambiente:
   - Copie o arquivo `.env.example` para `.env`
   - Preencha as variáveis com suas configurações reais:
     ```bash
     cp .env.example .env
     # Edite o .env com suas credenciais
     ```
   - **Importante**: O arquivo `.env` contém informações sensíveis e está incluído no `.gitignore` para não ser versionado.

### Variáveis de Ambiente

- `DB_HOST`: Host do banco de dados MySQL
- `DB_USER`: Usuário do banco de dados
- `DB_PASSWORD`: Senha do banco de dados
- `DB_DATABASE`: Nome do banco de dados
- `ARDUINO_PORT`: Porta serial do Arduino (padrão: COM6)
- `ARDUINO_BAUDRATE`: Baudrate da comunicação serial (padrão: 9600)
- `STREAM_URL`: URL do stream de vídeo ou índice da webcam (padrão: https://www.twitch.tv/gaules)

### Deploy na Nuvem

O projeto está configurado para deploy na plataforma Railway:

- O `railway.json` define as configurações de build e deploy.
- O `Dockerfile` garante que todas as dependências, incluindo Tesseract, sejam instaladas no container.
- O `runtime.txt` especifica a versão do Python.

Para deploy:
1. Conecte seu repositório ao Railway.
2. Configure as variáveis de ambiente na plataforma Railway.
3. Faça o deploy.

## Integração com Projeto Complementar

Este projeto foi desenvolvido para funcionar em conjunto com um sistema local que captura vídeo via webcam. O fluxo típico é:

1. **Sistema Local (Webcam)**: Captura vídeo da câmera e envia frames ou comandos para este sistema na nuvem.
2. **Sistema na Nuvem (Este projeto)**: Processa as imagens, verifica autorizações e controla dispositivos físicos remotamente.

## Segurança e Considerações

- A comunicação com Arduino é implementada com tratamento de erros; se o Arduino não estiver conectado, o sistema registra um aviso e continua funcionando (simulando a abertura para testes).
- Certifique-se de que o stream de vídeo seja acessível e legalmente autorizado.
- Monitore logs para auditoria e debugging.
- As credenciais são protegidas por variáveis de ambiente e não são versionadas.

## Contribuição

Para contribuir:
1. Fork o projeto.
2. Crie uma branch para sua feature.
3. Faça commit das mudanças.
4. Abra um Pull Request.

## Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.