import telebot
from telebot import types
import lyricsgenius
import os  # Essencial para ler as variáveis de ambiente

# O Render vai injetar esses valores que você acabou de configurar na interface
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GENIUS_TOKEN = os.environ.get("GENIUS_TOKEN")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genius = lyricsgenius.Genius(GENIUS_TOKEN)
genius.verbose = False 
# ... o restante do seu código continua abaixo ...

buscas_recentes = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Fala! Mande o nome da musica ou um trecho, e eu buscarei para voce.")

@bot.message_handler(func=lambda message: True)
def buscar_opcoes(message):
    status_msg = bot.reply_to(message, "?? Buscando...")
    
    # O search_songs busca tanto em titulos quanto em letras
    resultado = genius.search_songs(message.text, per_page=10)
    
    if not resultado or 'hits' not in resultado or len(resultado['hits']) == 0:
        bot.edit_message_text("? Nao encontrei nada com esse termo.", message.chat.id, status_msg.message_id)
        return

    markup = types.InlineKeyboardMarkup()
    for hit in resultado['hits']:
        song_title = hit['result']['title']
        artist = hit['result']['primary_artist']['name']
        song_id = hit['result']['id']
        
        buscas_recentes[f"song_{song_id}"] = song_id
        
        # Nome curto para caber no botao
        btn_text = f"{song_title[:25]} - {artist[:15]}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"song_{song_id}"))
    
    bot.edit_message_text("?? Escolha a musica correta:", message.chat.id, status_msg.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    song_id = buscas_recentes.get(call.data)
    if song_id:
        try:
            bot.answer_callback_query(call.id, "Carregando letra...")
            song = genius.search_song(song_id=song_id)
            
            # Limpeza basica da letra
            letra = song.lyrics.replace(f"{song.title} Lyrics", "").strip()
            resposta = f"*{song.title}*\n*Artista:* {song.artist}\n\n{letra}"
            
            # Divide se for grande demais
            if len(resposta) > 4096:
                for i in range(0, len(resposta), 4096):
                    bot.send_message(call.message.chat.id, resposta[i:i+4096])
            else:
                bot.send_message(call.message.chat.id, resposta, parse_mode="Markdown")
        except Exception:
            bot.send_message(call.message.chat.id, "Erro ao carregar a letra.")
    else:
        bot.send_message(call.message.chat.id, "Essa busca expirou. Tente pesquisar novamente.")

print("Melodify rodando...")
bot.polling()