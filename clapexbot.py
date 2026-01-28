import discord
from discord.ext import commands
import json
import os
import random
import asyncio
from flask import Flask
from threading import Thread
from discord.ui import View, Button, Select, Modal, TextInput
from datetime import datetime
import csv

# ---------- CONFIG ----------
TOKEN = ""  # ¡Reemplaza con tu token real!
DEFAULT_PREFIX = "?"
PREFIX_FILE = "prefix.json"
RANKING_FILE = "ranking.json"
WARN_FILE = "warns.json"
REACTION_ROLES_FILE = "reaction_roles.json"
CSV_FILE = "devoluciones.csv"

# Language settings
LANGUAGE_FILE = "language.json"
DEFAULT_LANGUAGE = "es"

# Usuarios permitidos para el comando csv
CSV_ALLOWED_USERS = [984268053141409813, 1345943525069553714, 556428548735238155]

# ---------- TRIVIA QUESTIONS ----------
TRIVIA_QUESTIONS = [
    {
        "pregunta": "¿Cuál es la capital de Francia?",
        "question": "What is the capital of France?",
        "respuesta": "paris",
        "answer": "paris",
        "dificultad": "facil",
        "difficulty": "easy",
        "puntos": 5,
        "points": 5
    },
    {
        "pregunta": "¿En qué año llegó el hombre a la luna?",
        "question": "In what year did man land on the moon?",
        "respuesta": "1969",
        "answer": "1969",
        "dificultad": "media",
        "difficulty": "medium",
        "puntos": 10,
        "points": 10
    },
    {
        "pregunta": "¿Quién pintó la Mona Lisa?",
        "question": "Who painted the Mona Lisa?",
        "respuesta": "leonardo da vinci",
        "answer": "leonardo da vinci",
        "dificultad": "media",
        "difficulty": "medium",
        "puntos": 10,
        "points": 10
    },
    {
        "pregunta": "¿Cuál es el río más largo del mundo?",
        "question": "What is the longest river in the world?",
        "respuesta": "amazonas",
        "answer": "amazon",
        "dificultad": "media",
        "difficulty": "medium",
        "puntos": 10,
        "points": 10
    },
    {
        "pregunta": "¿Cuál es el elemento químico con símbolo 'Au'?",
        "question": "What is the chemical element with the symbol 'Au'?",
        "respuesta": "oro",
        "answer": "gold",
        "dificultad": "facil",
        "difficulty": "easy",
        "puntos": 5,
        "points": 5
    },
    {
        "pregunta": "¿En qué continente se encuentra Egipto?",
        "question": "On which continent is Egypt located?",
        "respuesta": "africa",
        "answer": "africa",
        "dificultad": "facil",
        "difficulty": "easy",
        "puntos": 5,
        "points": 5
    },
    {
        "pregunta": "¿Cuántos lados tiene a heptágono?",
        "question": "How many sides does a heptagon have?",
        "respuesta": "7",
        "answer": "7",
        "dificultad": "media",
        "difficulty": "medium",
        "puntos": 10,
        "points": 10
    },
    {
        "pregunta": "¿Quién escribió 'Cien años de soledad'?",
        "question": "Who wrote 'One Hundred Years of Solitude'?",
        "respuesta": "gabriel garcia marquez",
        "answer": "gabriel garcia marquez",
        "dificultad": "media",
        "difficulty": "medium",
        "puntos": 10,
        "points": 10
    },
    {
        "pregunta": "¿Cuál es el planeta más grande del sistema solar?",
        "question": "What is the largest planet in the solar system?",
        "respuesta": "jupiter",
        "answer": "jupiter",
        "dificultad": "facil",
        "difficulty": "easy",
        "puntos": 5,
        "points": 5
    },
    {
        "pregunta": "¿En qué año comenzó la Segunda Guerra Mundial?",
        "question": "In what year did World War II begin?",
        "respuesta": "1939",
        "answer": "1939",
        "dificultad": "dificil",
        "difficulty": "hard",
        "puntos": 15,
        "points": 15
    }
]

# ---------- LANGUAGE SYSTEM ----------
def get_language(guild_id):
    if not os.path.exists(LANGUAGE_FILE):
        with open(LANGUAGE_FILE, "w") as f:
            json.dump({}, f)
    
    try:
        with open(LANGUAGE_FILE, "r") as f:
            data = json.load(f)
        return data.get(str(guild_id), DEFAULT_LANGUAGE)
    except:
        return DEFAULT_LANGUAGE

def set_language(guild_id, language):
    if not os.path.exists(LANGUAGE_FILE):
        with open(LANGUAGE_FILE, "w") as f:
            json.dump({}, f)
    
    try:
        with open(LANGUAGE_FILE, "r") as f:
            data = json.load(f)
        data[str(guild_id)] = language
        with open(LANGUAGE_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving language: {e}")

# ---------- PREFIJO ----------
def get_prefix(bot, message):
    if not message.guild:
        return DEFAULT_PREFIX
    
    if not os.path.exists(PREFIX_FILE):
        with open(PREFIX_FILE, "w") as f:
            json.dump({}, f)
    
    try:
        with open(PREFIX_FILE, "r") as f:
            data = json.load(f)
        return data.get(str(message.guild.id), DEFAULT_PREFIX)
    except:
        return DEFAULT_PREFIX

def set_prefix(guild_id, new_prefix):
    if not os.path.exists(PREFIX_FILE):
        with open(PREFIX_FILE, "w") as f:
            json.dump({}, f)
    
    try:
        with open(PREFIX_FILE, "r") as f:
            data = json.load(f)
        data[str(guild_id)] = new_prefix
        with open(PREFIX_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error al guardar prefijo: {e}")

# ---------- INTENTS ----------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.help_command = None

# ---------- RANKING ----------
def cargar_ranking():
    if not os.path.exists(RANKING_FILE):
        return {}
    try:
        with open(RANKING_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def guardar_ranking(ranking):
    with open(RANKING_FILE, "w") as f:
        json.dump(ranking, f, indent=4)

def sumar_puntos(user_id, username, cantidad=1):
    ranking = cargar_ranking()
    if str(user_id) not in ranking:
        ranking[str(user_id)] = {"username": username, "puntos": 0}
    ranking[str(user_id)]["puntos"] += cantidad
    guardar_ranking(ranking)

def restar_puntos(user_id, username, cantidad=1):
    ranking = cargar_ranking()
    if str(user_id) not in ranking:
        ranking[str(user_id)] = {"username": username, "puntos": 0}
    ranking[str(user_id)]["puntos"] -= cantidad
    guardar_ranking(ranking)

def obtener_ranking():
    ranking = cargar_ranking()
    return sorted(ranking.items(), key=lambda x: x[1]["puntos"], reverse=True)

def resetear_ranking():
    ranking = {}
    guardar_ranking(ranking)
    return True

# ---------- WARNINGS ----------
def cargar_warns():
    if not os.path.exists(WARN_FILE):
        return {}
    try:
        with open(WARN_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def guardar_warns(warns):
    with open(WARN_FILE, "w") as f:
        json.dump(warns, f, indent=4)

def migrar_warns_sin_id():
    """Migra warns antiguos que no tienen ID a la nueva estructura con ID"""
    warns = cargar_warns()
    migrado = False
    
    for user_id, user_warns in warns.items():
        for warn in user_warns:
            # Agregar ID si no existe
            if "id" not in warn:
                warn["id"] = obtener_proximo_id_warn(warns)
                migrado = True
            
            # Agregar fecha si no existe (usar fecha actual)
            if "fecha" not in warn:
                warn["fecha"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                migrado = True
            
            # Agregar autor si no existe (usar ID de sistema o 0)
            if "autor" not in warn:
                warn["autor"] = 0  # ID por defecto para autor desconocido
                migrado = True
            
            # Agregar razón si no existe
            if "razon" not in warn:
                warn["razon"] = "Razón no especificada"
                migrado = True
    
    if migrado:
        guardar_warns(warns)
        print("✅ Warns antiguos migrados a la nueva estructura completa")
    
    return warns

def obtener_proximo_id_warn(warns):
    max_id = 0
    for user_warns in warns.values():
        for warn in user_warns:
            if "id" in warn and warn["id"] > max_id:
                max_id = warn["id"]
    return max_id + 1

def eliminar_warn_por_id(warns, warn_id):
    for user_id, user_warns in warns.items():
        for i, warn in enumerate(user_warns):
            if "id" in warn and warn["id"] == warn_id:
                del user_warns[i]
                if not user_warns:
                    del warns[user_id]
                return True
    return False

# ---------- PERMISOS ----------
ROLES_PERMITIDOS = [1333150994506449079, 1375889672273924269, 1316944603642986637]
STAFF_ROLES = ROLES_PERMITIDOS + [1400338905856741507, 1323703676178530345]
ADMIN_ROLES = [1333150994506449079]  # Roles de administrador para el comando language

def tiene_permiso(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    return any(role.id in ROLES_PERMITIDOS for role in ctx.author.roles)

def tiene_permiso_staff(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    return any(role.id in STAFF_ROLES for role in ctx.author.roles)

def es_staff(member):
    if member.guild_permissions.administrator:
        return True
    return any(role.id in STAFF_ROLES for role in member.roles)

def es_admin(member):
    if member.guild_permissions.administrator:
        return True
    return any(role.id in ADMIN_ROLES for role in member.roles)

# ---------- CSV FUNCTIONS ----------
def inicializar_csv():
    """Inicializa el archivo CSV con los encabezados si no existe"""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='|')
            writer.writerow(['ID', 'Usuario', 'ID_Usuario', 'Rol', 'Dinero_Devuelto', 'Numero_Devolucion', 'Fecha'])

def agregar_fila_csv(usuario, id_usuario, rol, dinero_devuelto, numero_devolucion, fecha):
    """Agrega una nueva fila al archivo CSV"""
    try:
        inicializar_csv()
        
        # Obtener el próximo ID
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if len(lines) <= 1:  # Solo encabezados
                next_id = 1
            else:
                last_line = lines[-1].split('|')
                try:
                    next_id = int(last_line[0].strip()) + 1
                except ValueError:
                    next_id = 1
        
        with open(CSV_FILE, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='|')
            writer.writerow([f' {next_id} ', f' {usuario} ', f' {id_usuario} ', f' {rol} ', f' {dinero_devuelto} ', f' {numero_devolucion} ', f' {fecha} '])
        return True, "Datos agregados correctamente al CSV"
    except Exception as e:
        return False, f"Error al agregar datos al CSV: {str(e)}"

def obtener_csv_como_archivo():
    """Devuelve el archivo CSV como un objeto de archivo de Discord"""
    if os.path.exists(CSV_FILE):
        return discord.File(CSV_FILE, filename="devoluciones.csv")
    return None

def eliminar_fila_csv_por_id(fila_id):
    """Elimina una fila del CSV por ID"""
    try:
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        if len(lines) <= 1:  # Solo encabezados
            return False, "El archivo CSV está vacío"
        
        encontrado = False
        nuevas_lineas = [lines[0]]  # Mantener encabezados
        
        for i, line in enumerate(lines[1:], 1):
            partes = line.split('|')
            if len(partes) > 0:
                try:
                    id_actual = int(partes[0].strip())
                except ValueError:
                    continue
                if id_actual == fila_id:
                    encontrado = True
                else:
                    nuevas_lineas.append(line)
        
        if encontrado:
            with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
                file.writelines(nuevas_lineas)
            return True, f"Fila con ID {fila_id} eliminada correctamente"
        else:
            return False, f"No se encontró ninguna fila con ID {fila_id}"
    except Exception as e:
        return False, f"Error al eliminar fila del CSV: {str(e)}"

def reset_csv():
    """Resetea el archivo CSV a solo los encabezados"""
    try:
        with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='|')
            writer.writerow(['ID', 'Usuario', 'ID_Usuario', 'Rol', 'Dinero_Devuelto', 'Numero_Devolucion', 'Fecha'])
        return True, "CSV reseteado correctamente"
    except Exception as e:
        return False, f"Error al resetear CSV: {str(e)}"

# ---------- EVENTOS ----------
@bot.event
async def on_ready():
    print(f"✅ Bot conectado como {bot.user}")
    inicializar_csv()
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="https://www.youtube.com/@Atsuliver | ?help"
        )
    )
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos de barra diagonal sincronizados")
    except Exception as e:
        print(f"❌ Error al sincronizar comandos de barra diagonal: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        embed = discord.Embed(
            title="❌ Error de Permisos",
            description="No tienes permisos para ejecutar este comando.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            title="❌ Argumento Incorrecto",
            description="Revisa la sintaxis del comando.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(
            title="❌ Error",
            description="Ha ocurrido un error inesperado.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        print(f"Error no manejado: {error}")

# ---------- FUNCIONES AUX ----------
def parse_time_to_seconds(tiempo_str):
    multipliers = {"s":1,"m":60,"h":3600,"d":86400,"w":604800}
    try:
        unidad = tiempo_str[-1].lower()
        cantidad = int(tiempo_str[:-1])
        if unidad in multipliers:
            return cantidad * multipliers[unidad]
    except:
        return None
    return None

# ---------- RESET CONFIRMATION VIEWS ----------
class ResetCSVView(View):
    def __init__(self, ctx):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.value = None
    
    @discord.ui.button(label="✅", style=discord.ButtonStyle.success, custom_id="confirm_csv")
    async def confirm(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            lang = get_language(interaction.guild.id)
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description="These buttons are not for you.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Estos botones no son para ti.",
                    color=discord.Color.red()
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        self.value = True
        self.stop()
        
        success, message = reset_csv()
        lang = get_language(interaction.guild.id)
        
        if success:
            if lang == "en":
                embed = discord.Embed(
                    title="✅ CSV Reset",
                    description="CSV file has been successfully reset.",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="✅ CSV Reiniciado",
                    description="El archivo CSV ha sido reiniciado correctamente.",
                    color=discord.Color.green()
                )
        else:
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Error resetting CSV: {message}",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"Error al reiniciar CSV: {message}",
                    color=discord.Color.red()
                )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger, custom_id="cancel_csv")
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            lang = get_language(interaction.guild.id)
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description="These buttons are not for you.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Estos botones no son para ti.",
                    color=discord.Color.red()
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        self.value = False
        self.stop()
        
        lang = get_language(interaction.guild.id)
        if lang == "en":
            embed = discord.Embed(
                title="❌ Cancelled",
                description="CSV reset has been cancelled.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Cancelado",
                description="El reinicio del CSV ha sido cancelado.",
                color=discord.Color.red()
            )
        
        await interaction.response.edit_message(embed=embed, view=None)

class ResetRankingView(View):
    def __init__(self, ctx):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.value = None
    
    @discord.ui.button(label="✅", style=discord.ButtonStyle.success, custom_id="confirm_ranking")
    async def confirm(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            lang = get_language(interaction.guild.id)
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description="These buttons are not for you.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Estos botones no son para ti.",
                    color=discord.Color.red()
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        self.value = True
        self.stop()
        
        resetear_ranking()
        lang = get_language(interaction.guild.id)
        
        if lang == "en":
            embed = discord.Embed(
                title="✅ Ranking Reset",
                description="Ranking has been successfully reset.",
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="✅ Ranking Reiniciado",
                description="El ranking ha sido reiniciado correctamente.",
                color=discord.Color.green()
            )
        
        await interaction.response.edit_message(embed=embed, view=None)
    
    @discord.ui.button(label="❌", style=discord.ButtonStyle.danger, custom_id="cancel_ranking")
    async def cancel(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            lang = get_language(interaction.guild.id)
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description="These buttons are not for you.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Estos botones no son para ti.",
                    color=discord.Color.red()
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        self.value = False
        self.stop()
        
        lang = get_language(interaction.guild.id)
        if lang == "en":
            embed = discord.Embed(
                title="❌ Cancelled",
                description="Ranking reset has been cancelled.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Cancelado",
                description="El reinicio del ranking ha sido cancelado.",
                color=discord.Color.red()
            )
        
        await interaction.response.edit_message(embed=embed, view=None)

# ---------- LANGUAGE COMMAND ----------
@bot.hybrid_command(name="language", description="Change the bot's language / Cambia el idioma del bot")
async def language(ctx, lang: str):
    if not es_admin(ctx.author):
        lang = get_language(ctx.guild.id)
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permiso para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    lang = lang.lower()
    if lang not in ["es", "en", "english", "spanish", "español", "ingles"]:
        embed = discord.Embed(
            title="❌ Idioma no válido / Invalid language",
            description="Idiomas disponibles: es, en / Available languages: es, en",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Normalize language code
    if lang in ["en", "english", "ingles"]:
        lang_code = "en"
    else:
        lang_code = "es"
    
    set_language(ctx.guild.id, lang_code)
    
    if lang_code == "en":
        embed = discord.Embed(
            title="✅ Language Changed",
            description=f"Bot language changed to: English",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="✅ Idioma Cambiado",
            description=f"Idioma del bot cambiado a: Español",
            color=discord.Color.green()
        )
    
    await ctx.send(embed=embed)

# ---------- COMANDOS HÍBRIDOS ----------

# Comando prefix
@bot.hybrid_command(name="prefix", description="Cambia el prefijo del bot (Solo staff) / Change the bot's prefix (Staff only)")
async def prefix(ctx, nuevo_prefijo: str):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permiso para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    set_prefix(ctx.guild.id, nuevo_prefijo)
    
    if lang == "en":
        embed = discord.Embed(
            title="✅ Prefix Changed",
            description=f"Prefix changed to: {nuevo_prefijo}",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="✅ Prefijo Cambiado",
            description=f"Prefijo cambiado a: {nuevo_prefijo}",
            color=discord.Color.green()
        )
    await ctx.send(embed=embed)

# Comando announce
@bot.hybrid_command(name="announce", description="Hace un anuncio oficial (Solo staff) / Make an official announcement (Staff only)")
async def announce(ctx, canal: discord.TextChannel, *, mensaje: str):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permiso para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    if lang == "en":
        embed = discord.Embed(title="📢 Official Announcement", description=mensaje, color=discord.Color.red(), timestamp=datetime.now())
        embed.set_footer(text=f"Announced by {ctx.author.display_name}")
    else:
        embed = discord.Embed(title="📢 Anuncio Oficial", description=mensaje, color=discord.Color.red(), timestamp=datetime.now())
        embed.set_footer(text=f"Anunciado por {ctx.author.display_name}")
    
    await canal.send(embed=embed)
    
    if lang == "en":
        confirm_embed = discord.Embed(
            title="✅ Announcement Sent",
            description="The announcement has been sent successfully.",
            color=discord.Color.green()
        )
    else:
        confirm_embed = discord.Embed(
            title="✅ Anuncio Enviado",
            description="El anuncio ha sido enviado correctamente.",
            color=discord.Color.green()
        )
    await ctx.send(embed=confirm_embed, ephemeral=True)

# ---------- AUTOROLE ----------
def cargar_reaction_roles():
    if not os.path.exists(REACTION_ROLES_FILE):
        return {}
    try:
        with open(REACTION_ROLES_FILE,"r") as f:
            return json.load(f)
    except:
        return {}

def guardar_reaction_roles(data):
    with open(REACTION_ROLES_FILE,"w") as f:
        json.dump(data,f,indent=4)

@bot.hybrid_command(name="autorole", description="Configura un autorol / Set up an autorole")
async def autorole(ctx, canal: discord.TextChannel, mensaje_id: str, emoji: str, rol: discord.Role):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permiso para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    try:
        mensaje_int = int(mensaje_id)
        mensaje = await canal.fetch_message(mensaje_int)
    except (ValueError, discord.NotFound):
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="Message not found in the specified channel or ID is invalid.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No se encontró el mensaje en el canal especificado o el ID es inválido.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Procesar emoji personalizado
    emoji_to_store = emoji
    if emoji.startswith('<') and emoji.endswith('>'):
        emoji_parts = emoji.strip('<>').split(':')
        if len(emoji_parts) >= 2:
            emoji_to_store = emoji_parts[1] if not emoji_parts[0] else emoji_parts[1]
    
    data = cargar_reaction_roles()
    data[str(mensaje_id)] = {"emoji": emoji_to_store, "rol_id": rol.id, "canal_id": canal.id}
    guardar_reaction_roles(data)
    
    try:
        await mensaje.add_reaction(emoji)
        if lang == "en":
            embed = discord.Embed(
                title="✅ Autorole Configured",
                description=f"Autorole configured: {emoji} → {rol.name}",
                color=discord.Color.green()
            )
            embed.add_field(name="Channel", value=canal.mention, inline=True)
            embed.add_field(name="Message ID", value=mensaje_id, inline=True)
        else:
            embed = discord.Embed(
                title="✅ Autorol Configurado",
                description=f"Autorol configurado: {emoji} → {rol.name}",
                color=discord.Color.green()
            )
            embed.add_field(name="Canal", value=canal.mention, inline=True)
            embed.add_field(name="Mensaje ID", value=mensaje_id, inline=True)
        await ctx.send(embed=embed, ephemeral=True)
    except discord.Forbidden:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="I don't have permissions to add reactions in that channel.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No tengo permisos para añadir reacciones en ese canal.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    
    data = cargar_reaction_roles()
    if str(payload.message_id) in data:
        info = data[str(payload.message_id)]
        
        emoji_compare = payload.emoji.name
        if payload.emoji.id:
            emoji_compare = payload.emoji.name
        
        if emoji_compare == info["emoji"]:
            guild = bot.get_guild(payload.guild_id)
            if not guild:
                return
            
            rol = guild.get_role(info["rol_id"])
            miembro = guild.get_member(payload.user_id)
            
            if rol and miembro:
                await miembro.add_roles(rol)

@bot.event
async def on_raw_reaction_remove(payload):
    data = cargar_reaction_roles()
    if str(payload.message_id) in data:
        info = data[str(payload.message_id)]
        
        emoji_compare = payload.emoji.name
        if payload.emoji.id:
            emoji_compare = payload.emoji.name
        
        if emoji_compare == info["emoji"]:
            guild = bot.get_guild(payload.guild_id)
            if not guild:
                return
            
            rol = guild.get_role(info["rol_id"])
            miembro = guild.get_member(payload.user_id)
            
            if rol and miembro:
                await miembro.remove_roles(rol)

# ---------- RANKING ----------
@bot.hybrid_command(name="addpoints", description="Añade puntos a un usuario (Solo staff) / Add points to a user (Staff only)")
async def addpoints(ctx, member: discord.Member, cantidad: int):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permiso para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    sumar_puntos(member.id, member.name, cantidad)
    
    if lang == "en":
        embed = discord.Embed(
            title="✅ Points Added",
            description=f"**{cantidad}** points have been added to {member.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="User", value=member.display_name, inline=True)
        embed.add_field(name="Points added", value=cantidad, inline=True)
        embed.add_field(name="By", value=ctx.author.mention, inline=True)
    else:
        embed = discord.Embed(
            title="✅ Puntos Agregados",
            description=f"Se le agregaron **{cantidad}** puntos a {member.mention}",
            color=discord.Color.green()
        )
        embed.add_field(name="Usuario", value=member.display_name, inline=True)
        embed.add_field(name="Puntos agregados", value=cantidad, inline=True)
        embed.add_field(name="Por", value=ctx.author.mention, inline=True)
    
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/998805272585510962.png")  # Emoji de verificado
    
    await ctx.send(embed=embed)

@addpoints.error
async def addpoints_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        lang = get_language(ctx.guild.id)
        if lang == "en":
            embed = discord.Embed(
                title="❌ Missing Argument",
                description="You must specify the amount of points to add.\nUsage: `/addpoints @user amount`",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Argumento Faltante",
                description="Debes especificar la cantidad de puntos a agregar.\nUso: `/addpoints @usuario cantidad`",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)

@bot.hybrid_command(name="removepoints", description="Quita puntos a un usuario (Solo staff) / Remove points from a user (Staff only)")
async def removepoints(ctx, member: discord.Member, cantidad: str):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Verificar si se quiere quitar todos los puntos
    if cantidad.lower() == "all":
        ranking = cargar_ranking()
        if str(member.id) in ranking:
            puntos_actuales = ranking[str(member.id)]["puntos"]
            restar_puntos(member.id, member.name, puntos_actuales)
            
            if lang == "en":
                embed = discord.Embed(
                    title="❌ All Points Removed",
                    description=f"All **{puntos_actuales}** points have been removed from {member.mention}",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Todos los Puntos Removidos",
                    description=f"Se le restaron todos los **{puntos_actuales}** puntos a {member.mention}",
                    color=discord.Color.red()
                )
        else:
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"{member.mention} doesn't have any points.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description=f"{member.mention} no tiene puntos.",
                    color=discord.Color.red()
                )
    else:
        try:
            cantidad_int = int(cantidad)
            restar_puntos(member.id, member.name, cantidad_int)
            
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Points Removed",
                    description=f"**{cantidad_int}** points have been removed from {member.mention}",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Puntos Removidos",
                    description=f"Se le restaron **{cantidad_int}** puntos a {member.mention}",
                    color=discord.Color.red()
                )
        except ValueError:
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description="Please enter a valid number or 'all' to remove all points.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Por favor ingresa un número válido o 'all' para quitar todos los puntos.",
                    color=discord.Color.red()
                )
            await ctx.send(embed=embed, ephemeral=True)
            return
    
    embed.add_field(name="User", value=member.display_name, inline=True)
    embed.add_field(name="Points removed", value=cantidad, inline=True)
    embed.add_field(name="By", value=ctx.author.mention, inline=True)
    
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/998805272585510962.png")  # Emoji de cruz
    
    await ctx.send(embed=embed)

@removepoints.error
async def removepoints_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        lang = get_language(ctx.guild.id)
        if lang == "en":
            embed = discord.Embed(
                title="❌ Missing Argument",
                description="You must specify the amount of points to remove.\nUsage: `/removepoints @user amount` or `/removepoints @user all`",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Argumento Faltante",
                description="Debes especificar la cantidad de puntos a quitar.\nUso: `/removepoints @usuario cantidad` o `/removepoints @usuario all`",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)

@bot.hybrid_command(name="ranking", description="Muestra el ranking de puntos / Shows the points ranking")
async def ranking(ctx, action: str = None):
    lang = get_language(ctx.guild.id)
    
    # Comando para resetear el ranking
    if action and action.lower() == "reset":
        if not tiene_permiso_staff(ctx):
            if lang == "en":
                embed = discord.Embed(
                    title="❌ No Permissions",
                    description="You don't have permission to use this command.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Sin Permisos",
                    description="No tienes permisos para usar este comando.",
                    color=discord.Color.red()
                )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        if lang == "en":
            embed = discord.Embed(
                title="⚠️ Reset Ranking",
                description="Are you sure you want to reset the ranking? This action cannot be undone.",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title="⚠️ Reiniciar Ranking",
                description="¿Estás seguro de que quieres reiniciar el ranking? Esta acción no se puede deshacer.",
                color=discord.Color.orange()
            )
        
        view = ResetRankingView(ctx)
        await ctx.send(embed=embed, view=view)
        return
    
    # Comando normal para mostrar el ranking
    top = obtener_ranking()
    if not top:
        if lang == "en":
            embed = discord.Embed(
                title="😢 Empty Ranking",
                description="Nobody has points yet.",
                color=discord.Color.blue()
            )
        else:
            embed = discord.Embed(
                title="😢 Ranking Vacío",
                description="Nadie tiene puntos todavía.",
                color=discord.Color.blue()
            )
        await ctx.send(embed=embed)
        return
    
    if lang == "en":
        embed = discord.Embed(title="🏆 General Ranking", color=discord.Color.gold())
    else:
        embed = discord.Embed(title="🏆 Ranking General", color=discord.Color.gold())
    
    for i, (user_id, data) in enumerate(top[:10], start=1):
        medal = "👑" if i==1 else "🥈" if i==2 else "🥉" if i==3 else "⭐"
        if lang == "en":
            embed.add_field(name=f"{i}. {medal} {data['username']}", value=f"{data['puntos']} points", inline=False)
        else:
            embed.add_field(name=f"{i}. {medal} {data['username']}", value=f"{data['puntos']} puntos", inline=False)
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name="rank", description="Muestra los puntos y posición de un usuario / Shows a user's points and position")
async def rank(ctx, member: discord.Member = None):
    lang = get_language(ctx.guild.id)
    
    member = member or ctx.author
    ranking_data = obtener_ranking()
    
    for i, (user_id, data) in enumerate(ranking_data, start=1):
        if str(member.id) == user_id:
            if lang == "en":
                embed = discord.Embed(title=f"👤 Profile of {data['username']}", color=discord.Color.blue())
                embed.add_field(name="⭐ Points", value=data["puntos"], inline=True)
                embed.add_field(name="🏅 Position", value=f"#{i}", inline=True)
            else:
                embed = discord.Embed(title=f"👤 Perfil de {data['username']}", color=discord.Color.blue())
                embed.add_field(name="⭐ Puntos", value=data["puntos"], inline=True)
                embed.add_field(name="🏅 Posición", value=f"# i", inline=True)
            await ctx.send(embed=embed)
            return
    
    if lang == "en":
        embed = discord.Embed(
            title="📊 No Points",
            description=f"{member.mention} doesn't have points yet.",
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title="📊 Sin Puntos",
            description=f"{member.mention} todavía no tiene puntos.",
            color=discord.Color.blue()
        )
    await ctx.send(embed=embed)

# ---------- TRIVIA ----------
@bot.hybrid_command(name="trivia", description="Inicia una trivia con preguntas aleatorias / Starts a trivia with random questions")
async def trivia(ctx, dificultad: str = None):
    lang = get_language(ctx.guild.id)
    
    """Inicia una trivia con preguntas aleatorias"""
    # Normalizar dificultad (quitar tildes)
    if dificultad:
        dificultad_norm = dificultad.lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        if lang == "en":
            if dificultad_norm not in ["easy", "medium", "hard"]:
                embed = discord.Embed(
                    title="❌ Invalid Difficulty",
                    description="Use: easy, medium or hard",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed, ephemeral=True)
                return
        else:
            if dificultad_norm not in ["facil", "media", "dificil"]:
                embed = discord.Embed(
                    title="❌ Dificultad Inválida",
                    description="Usa: facil, media o dificil",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed, ephemeral=True)
                return
        dificultad = dificultad_norm
    
    # Filtrar preguntas por dificultad
    if dificultad:
        if lang == "en":
            # Map English difficulty to Spanish for filtering
            difficulty_map = {"easy": "facil", "medium": "media", "hard": "dificil"}
            preguntas_filtradas = [q for q in TRIVIA_QUESTIONS if q["dificultad"] == difficulty_map.get(dificultad, dificultad)]
        else:
            preguntas_filtradas = [q for q in TRIVIA_QUESTIONS if q["dificultad"] == dificultad]
    else:
        preguntas_filtradas = TRIVIA_QUESTIONS
    
    if not preguntas_filtradas:
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Questions",
                description="There are no questions available for that difficulty.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Preguntas",
                description="No hay preguntas disponibles para esa dificultad.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    pregunta_obj = random.choice(preguntas_filtradas)
    
    if lang == "en":
        embed = discord.Embed(title="🎯 Trivia", color=discord.Color.blue())
        embed.add_field(name="Question", value=pregunta_obj["question"], inline=False)
        embed.add_field(name="Difficulty", value=pregunta_obj["difficulty"].capitalize(), inline=True)
        embed.add_field(name="Points", value=pregunta_obj["points"], inline=True)
        embed.add_field(name="Time", value="30 seconds", inline=True)
        embed.set_footer(text="Answer with the correct answer!")
    else:
        embed = discord.Embed(title="🎯 Trivia", color=discord.Color.blue())
        embed.add_field(name="Pregunta", value=pregunta_obj["pregunta"], inline=False)
        embed.add_field(name="Dificultad", value=pregunta_obj["dificultad"].capitalize(), inline=True)
        embed.add_field(name="Puntos", value=pregunta_obj["puntos"], inline=True)
        embed.add_field(name="Tiempo", value="30 segundos", inline=True)
        embed.set_footer(text="Responde con la respuesta correcta!")
    
    await ctx.send(embed=embed)
    
    def check(m):
        return m.channel == ctx.channel and not m.author.bot
    
    try:
        while True:
            msg = await bot.wait_for("message", timeout=30, check=check)
            # Normalizar respuesta (quitar tildes y espacios extras)
            respuesta_usuario = msg.content.lower().strip().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            
            # Check answer based on language
            correct_answer = pregunta_obj["respuesta"] if lang != "en" else pregunta_obj["answer"]
            
            if respuesta_usuario == correct_answer:
                if lang == "en":
                    embed_correcto = discord.Embed(
                        title="✅ Correct Answer",
                        description=f"Correct, {msg.author.mention}!",
                        color=discord.Color.green()
                    )
                else:
                    embed_correcto = discord.Embed(
                        title="✅ Respuesta Correcta",
                        description=f"¡Correcto, {msg.author.mention}!",
                        color=discord.Color.green()
                    )
                await ctx.send(embed=embed_correcto)
                break
            else:
                if lang == "en":
                    embed_incorrecto = discord.Embed(
                        title="❌ Incorrect Answer",
                        description="Keep trying!",
                        color=discord.Color.red()
                    )
                else:
                    embed_incorrecto = discord.Embed(
                        title="❌ Respuesta Incorrecta",
                        description="Sigue intentando!",
                        color=discord.Color.red()
                    )
                await ctx.send(embed=embed_incorrecto)
    except asyncio.TimeoutError:
        correct_answer = pregunta_obj["respuesta"] if lang != "en" else pregunta_obj["answer"]
        if lang == "en":
            embed_timeout = discord.Embed(
                title="⏰ Time's Up",
                description=f"The correct answer was: **{correct_answer}**",
                color=discord.Color.orange()
            )
        else:
            embed_timeout = discord.Embed(
                title="⏰ Tiempo Agotado",
                description=f"La respuesta correcta era: **{correct_answer}**",
                color=discord.Color.orange()
            )
        await ctx.send(embed=embed_timeout)

# Comando pregunta
@bot.hybrid_command(name="pregunta", description="Crea una pregunta de trivia / Create a trivia question")
async def pregunta(ctx, canal: discord.TextChannel, pregunta: str, respuesta_correcta: str, tiempo: int, premio: int):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permiso para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    if tiempo < 5 or tiempo > 600:
        if lang == "en":
            embed = discord.Embed(
                title="⏱️ Invalid Time",
                description="Time must be between 5 seconds and 10 minutes.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="⏱️ Tiempo Inválido",
                description="El tiempo debe estar entre 5 segundos y 10 minutos.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Embed para la pregunta con formato mejorado
    if lang == "en":
        question_embed = discord.Embed(
            title="🎯 New Trivia Question",
            color=discord.Color.blue()
        )
        question_embed.add_field(name="**Question**", value=f"**{pregunta}**", inline=False)
        question_embed.add_field(name="⏳ Time", value=f"{tiempo} seconds", inline=True)
        question_embed.add_field(name="💰 Reward", value=f"{premio} points", inline=True)
        question_embed.set_footer(text="Answer correctly to win points!")
    else:
        question_embed = discord.Embed(
            title="🎯 Nueva Pregunta de Trivia",
            color=discord.Color.blue()
        )
        question_embed.add_field(name="**Pregunta**", value=f"**{pregunta}**", inline=False)
        question_embed.add_field(name="⏳ Tiempo", value=f"{tiempo} segundos", inline=True)
        question_embed.add_field(name="💰 Premio", value=f"{premio} puntos", inline=True)
        question_embed.set_footer(text="Responde correctamente para ganar puntos!")
    
    await canal.send(embed=question_embed)
    
    if lang == "en":
        confirm_embed = discord.Embed(
            title="✅ Question Sent",
            description="The question has been sent successfully.",
            color=discord.Color.green()
        )
    else:
        confirm_embed = discord.Embed(
            title="✅ Pregunta Enviada",
            description="La pregunta ha sido enviada correctamente.",
            color=discord.Color.green()
        )
    await ctx.send(embed=confirm_embed, ephemeral=True)

    def check(m):
        return m.channel == canal and not m.author.bot

    try:
        while True:
            msg = await bot.wait_for("message", timeout=tiempo, check=check)
            if msg.content.lower().strip() == respuesta_correcta.lower().strip():
                sumar_puntos(msg.author.id, msg.author.name, premio)
                
                if lang == "en":
                    embed_correcto = discord.Embed(
                        title="✅ Correct Answer",
                        description=f"Correct, {msg.author.mention}! You won {premio} points.",
                        color=discord.Color.green()
                    )
                    embed_correcto.add_field(name="To claim", value="Open a ticket in <#1322787534878806111>", inline=False)
                else:
                    embed_correcto = discord.Embed(
                        title="✅ Respuesta Correcta",
                        description=f"¡Correcto, {msg.author.mention}! Ganaste {premio} puntos.",
                        color=discord.Color.green()
                    )
                    embed_correcto.add_field(name="Para reclamar", value="Abre un ticket en <#1322787534878806111>", inline=False)
                await canal.send(embed=embed_correcto)
                break
            else:
                if lang == "en":
                    embed_incorrecto = discord.Embed(
                        title="❌ Incorrect Answer",
                        description="Keep trying!",
                        color=discord.Color.red()
                    )
                else:
                    embed_incorrecto = discord.Embed(
                        title="❌ Respuesta Incorrecta",
                        description="Sigue intentando!",
                        color=discord.Color.red()
                    )
                await canal.send(embed=embed_incorrecto)
    except asyncio.TimeoutError:
        if lang == "en":
            embed_timeout = discord.Embed(
                title="⏰ Time's Up",
                description=f"No one answered correctly.\n\nThe correct answer was: **{respuesta_correcta}**",
                color=discord.Color.orange()
            )
        else:
            embed_timeout = discord.Embed(
                title="⏰ Tiempo Agotado",
                description=f"Nadie respondió correctamente.\n\nLa respuesta correcta era: **{respuesta_correcta}**",
                color=discord.Color.orange()
            )
        await canal.send(embed=embed_timeout)

@pregunta.error
async def pregunta_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        lang = get_language(ctx.guild.id)
        if lang == "en":
            embed = discord.Embed(
                title="❌ Missing Arguments",
                description="You must specify all required parameters.\nUsage: `/pregunta #channel question correct_answer time reward`",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Argumentos Faltantes",
                description="Debes especificar todos los parámetros requeridos.\nUso: `/pregunta #canal pregunta respuesta_correcta tiempo premio`",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)

# ---------- WARNINGS ----------
class DeleteWarnModal(Modal, title="Eliminar Advertencia / Delete Warning"):
    def __init__(self, view):
        super().__init__()
        self.view = view
        self.warn_id = TextInput(
            label="ID de la advertencia a eliminar / ID of the warning to delete",
            placeholder="Ingresa el número de advertencia / Enter the warning number",
            required=True
        )
        self.add_item(self.warn_id)

    async def on_submit(self, interaction: discord.Interaction):
        lang = get_language(interaction.guild.id)
        
        try:
            warn_id = int(self.warn_id.value)
            warns = cargar_warns()
            
            if eliminar_warn_por_id(warns, warn_id):
                guardar_warns(warns)
                if lang == "en":
                    embed = discord.Embed(
                        title="✅ Warning Deleted",
                        description=f"Warning #{warn_id} deleted successfully.",
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title="✅ Advertencia Eliminada",
                        description=f"Advertencia #{warn_id} eliminada correctamente.",
                        color=discord.Color.green()
                    )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
                # Actualizar la vista de warnings
                if self.view and hasattr(self.view, 'create_embed'):
                    new_embed = self.view.create_embed()
                    await interaction.message.edit(embed=new_embed, view=self.view)
            else:
                if lang == "en":
                    embed = discord.Embed(
                        title="❌ Error",
                        description=f"No warning found with ID #{warn_id}.",
                        color=discord.Color.red()
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Error",
                        description=f"No se encontró ninguna advertencia con ID #{warn_id}.",
                        color=discord.Color.red()
                    )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except ValueError:
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description="Please enter a valid number.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Por favor ingresa un número válido.",
                    color=discord.Color.red()
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class WarningsView(View):
    def __init__(self, ctx, member, warns):
        super().__init__(timeout=180)  # Timeout de 3 minutos
        self.ctx = ctx
        self.member = member
        self.warns = warns
        self.current_page = 0
        self.warns_per_page = 5
    
    def create_embed(self):
        lang = get_language(self.ctx.guild.id)
        total_pages = (len(self.warns) - 1) // self.warns_per_page + 1
        start_idx = self.current_page * self.warns_per_page
        end_idx = min(start_idx + self.warns_per_page, len(self.warns))
        
        if lang == "en":
            embed = discord.Embed(
                title=f"⚠️ Warnings of {self.member.display_name}",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title=f"⚠️ Warns de {self.member.display_name}",
                color=discord.Color.orange()
            )
        
        # Agregar thumbnail con el avatar del usuario
        if self.member.avatar:
            embed.set_thumbnail(url=self.member.avatar.url)
        elif self.member.default_avatar:
            embed.set_thumbnail(url=self.member.default_avatar.url)
        
        if lang == "en":
            embed.add_field(
                name="👤 User",
                value=f"{self.member.mention} (`{self.member.id}`)",
                inline=False
            )
            
            # Mostrar cantidad de warns con cuadradito pequeño
            embed.add_field(
                name=f"📊 Number of warnings: `{len(self.warns)}`",
                value="\u200b",
                inline=False
            )
        else:
            embed.add_field(
                name="👤 Usuario",
                value=f"{self.member.mention} (`{self.member.id}`)",
                inline=False
            )
            
            # Mostrar cantidad de warns con cuadradito pequeño
            embed.add_field(
                name=f"📊 Cantidad de warns: `{len(self.warns)}`",
                value="\u200b",
                inline=False
            )
        
        for i in range(start_idx, end_idx):
            warn = self.warns[i]
            warn_date = datetime.strptime(warn["fecha"], "%d/%m/%Y %H:%M:%S")
            moderator = self.ctx.guild.get_member(warn["autor"])
            moderator_name = moderator.display_name if moderator else "Desconocido"
            
            if lang == "en":
                embed.add_field(
                    name=f" Warn | {warn_date.strftime('%d/%m/%Y')} | ID: {warn['id']}",
                    value=f"**Moderator:** {moderator_name}\n**Reason:** {warn['razon']}",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f" Warn | {warn_date.strftime('%d/%m/%Y')} | ID: {warn['id']}",
                    value=f"**Moderador:** {moderator_name}\n**Razón:** {warn['razon']}",
                    inline=False
                )
        
        if lang == "en":
            embed.set_footer(text=f"Page {self.current_page + 1}/{total_pages} • Total: {len(self.warns)} warnings")
        else:
            embed.set_footer(text=f"Página {self.current_page + 1}/{total_pages} • Total: {len(self.warns)} warns")
        return embed
    
    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary, custom_id="prev_page")
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            lang = get_language(interaction.guild.id)
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description="These buttons are not for you.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Estos botones no son para ti.",
                    color=discord.Color.red()
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary, custom_id="next_page")
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            lang = get_language(interaction.guild.id)
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description="These buttons are not for you.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Estos botones no son para ti.",
                    color=discord.Color.red()
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        total_pages = (len(self.warns) - 1) // self.warns_per_page + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Eliminar / Delete", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="delete_warn")
    async def delete_warn(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            lang = get_language(interaction.guild.id)
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description="These buttons are not for you.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Estos botones no son para ti.",
                    color=discord.Color.red()
                )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        modal = DeleteWarnModal(self)
        await interaction.response.send_modal(modal)

@bot.hybrid_command(name="warn", description="Advierte a un usuario (Solo staff) / Warn a user (Staff only)")
async def warn(ctx, usuario: str, *, razón: str):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Intentar obtener el miembro por mención o ID
    try:
        # Verificar si es una mención
        if usuario.startswith('<@') and usuario.endswith('>'):
            user_id = usuario.strip('<@!>')
            member = await ctx.guild.fetch_member(int(user_id))
        else:
            # Verificar si es un ID de usuario
            try:
                member = await ctx.guild.fetch_member(int(usuario))
            except ValueError:
                # Si no es un ID, buscar por nombre
                members = ctx.guild.members
                member = discord.utils.find(lambda m: m.name.lower() == usuario.lower() or m.display_name.lower() == usuario.lower(), members)
                
                if not member:
                    if lang == "en":
                        embed = discord.Embed(
                            title="❌ User Not Found",
                            description="User not found in this server.",
                            color=discord.Color.red()
                        )
                    else:
                        embed = discord.Embed(
                            title="❌ Usuario No Encontrado",
                            description="Usuario no encontrado en este servidor.",
                            color=discord.Color.red()
                        )
                    await ctx.send(embed=embed, ephemeral=True)
                    return
    except discord.NotFound:
        if lang == "en":
            embed = discord.Embed(
                title="❌ User Not Found",
                description="User not found in this server.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Usuario No Encontrado",
                description="Usuario no encontrado en este servidor.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    if not razón:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="You must specify a reason.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Debes especificar una razón.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    warns = migrar_warns_sin_id()
    user_warns = warns.get(str(member.id), [])
    
    next_id = obtener_proximo_id_warn(warns)
    
    user_warns.append({
        "id": next_id,
        "autor": ctx.author.id, 
        "razon": razón,
        "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    })
    warns[str(member.id)] = user_warns
    
    guardar_warns(warns)
    
    # Embed simple con solo la información básica
    if lang == "en":
        embed = discord.Embed(
            title="⚠️ Warn applied",
            color=discord.Color.gold(),
            description=f"{member.mention} has been warned"
        )
        embed.add_field(name="📝 Reason", value=razón, inline=True)
        embed.add_field(name="📅 Date", value=datetime.now().strftime("%d/%m/%Y %H:%M:%S"), inline=True)
    else:
        embed = discord.Embed(
            title="⚠️ Warn aplicado",
            color=discord.Color.gold(),
            description=f"Se ha advertido a {member.mention}"
        )
        embed.add_field(name="📝 Razón", value=razón, inline=True)
        embed.add_field(name="📅 Fecha", value=datetime.now().strftime("%d/%m/%Y %H:%M:%S"), inline=True)
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name="warnings", description="Muestra las advertencias de un usuario (Solo staff) / Shows a user's warnings (Staff only)")
async def warnings(ctx, member: discord.Member):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    warns = migrar_warns_sin_id()
    user_warns = warns.get(str(member.id), [])
    
    if not user_warns:
        # Embed verde con tilde para usuario sin warns
        if lang == "en":
            embed = discord.Embed(
                title="✅ No warnings",
                color=discord.Color.green(),
                description=f"{member.mention} has no warnings."
            )
        else:
            embed = discord.Embed(
                title="✅ Sin warns",
                color=discord.Color.green(),
                description=f"{member.mention} no tiene warns."
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    view = WarningsView(ctx, member, user_warns)
    embed = view.create_embed()
    view.message = await ctx.send(embed=embed, view=view)
    
class AllWarningsView(View):
    def __init__(self, ctx, warns_data, warns_per_page=7):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.warns_data = warns_data  # Lista de todos los warns
        self.warns_per_page = warns_per_page
        self.current_page = 0
        self.total_pages = (len(warns_data) - 1) // warns_per_page + 1
    
    def create_embed(self):
        lang = get_language(self.ctx.guild.id)
        start_idx = self.current_page * self.warns_per_page
        end_idx = min(start_idx + self.warns_per_page, len(self.warns_data))
        
        if lang == "en":
            embed = discord.Embed(
                title=f"⚠️ All Warnings ({len(self.warns_data)} total)",
                color=discord.Color.orange()
            )
        else:
            embed = discord.Embed(
                title=f"⚠️ Todos los Warns ({len(self.warns_data)} total)",
                color=discord.Color.orange()
            )
        
        # Mostrar warns de esta página (más nuevos primero)
        for i in range(start_idx, end_idx):
            warn = self.warns_data[i]
            user_id = warn["user_id"]
            member = self.ctx.guild.get_member(int(user_id))
            
            # Manejar campos
            fecha_str = warn.get("fecha", "Fecha desconocida")
            autor_id = warn.get("autor", 0)
            razon = warn.get("razon", "Razón no especificada")
            
            # Formatear fecha
            try:
                if fecha_str != "Fecha desconocida":
                    warn_date = datetime.strptime(fecha_str, "%d/%m/%Y %H:%M:%S")
                    fecha_str = warn_date.strftime('%d/%m/%Y %H:%M')
            except:
                pass
            
            # Obtener moderador
            moderator = self.ctx.guild.get_member(autor_id)
            if moderator:
                moderator_name = moderator.display_name
            elif autor_id == 0:
                moderator_name = "Sistema/Desconocido"
            else:
                moderator_name = f"Usuario {autor_id}"
            
            if lang == "en":
                embed.add_field(
                    name=f"🔰 {fecha_str} - ID: {warn['id']}",
                    value=f"**User:** {member.mention if member else f'User {user_id}'}\n**Moderator:** {moderator_name}\n**Reason:** {razon}",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"🔰 {fecha_str} - ID: {warn['id']}",
                    value=f"**Usuario:** {member.mention if member else f'Usuario {user_id}'}\n**Moderador:** {moderator_name}\n**Razón:** {razon}",
                    inline=False
                )
        
        if lang == "en":
            embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages} • Requested by {self.ctx.author.display_name}")
        else:
            embed.set_footer(text=f"Página {self.current_page + 1}/{self.total_pages} • Solicitado por {self.ctx.author.display_name}")
        
        return embed
    
    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.primary, custom_id="prev_page")
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            lang = get_language(interaction.guild.id)
            if lang == "en":
                await interaction.response.send_message("These buttons are not for you.", ephemeral=True)
            else:
                await interaction.response.send_message("Estos botones no son para ti.", ephemeral=True)
            return
        
        if self.current_page > 0:
            self.current_page -= 1
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="➡️", style=discord.ButtonStyle.primary, custom_id="next_page")
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.ctx.author.id:
            lang = get_language(interaction.guild.id)
            if lang == "en":
                await interaction.response.send_message("These buttons are not for you.", ephemeral=True)
            else:
                await interaction.response.send_message("Estos botones no son para ti.", ephemeral=True)
            return
        
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            embed = self.create_embed()
            await interaction.response.edit_message(embed=embed, view=self)

@bot.hybrid_command(name="allwarnings", description="Muestra todas las advertencias del servidor (Solo staff) / Shows all server warnings (Staff only)")
async def allwarnings(ctx):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    warns = migrar_warns_sin_id()
    
    if not warns:
        if lang == "en":
            embed = discord.Embed(
                title="✅ No warnings",
                color=discord.Color.green(),
                description="There are no warnings on the server."
            )
        else:
            embed = discord.Embed(
                title="✅ Sin warns",
                color=discord.Color.green(),
                description="No hay warns en el servidor."
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Convertir warns a lista plana y ordenar por fecha (más nuevos primero)
    all_warns = []
    for user_id, user_warns in warns.items():
        for warn in user_warns:
            # Agregar user_id a cada warn para referencia
            warn_with_user = warn.copy()
            warn_with_user["user_id"] = user_id
            all_warns.append(warn_with_user)
    
    # Ordenar por fecha (más nuevos primero)
    def get_warn_date(warn):
        try:
            return datetime.strptime(warn.get("fecha", ""), "%d/%m/%Y %H:%M:%S")
        except:
            return datetime.min  # Si no tiene fecha válida, poner al final
    
    all_warns.sort(key=get_warn_date, reverse=True)
    
    # Crear vista de paginación
    view = AllWarningsView(ctx, all_warns, warns_per_page=7)
    embed = view.create_embed()
    
    await ctx.send(embed=embed, view=view)

@bot.hybrid_command(name="delwarn", description="Elimina una advertencia por ID (Solo staff) / Delete a warning by ID (Staff only)")
async def delwarn(ctx, warn_id: int):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    warns = cargar_warns()
    
    # Migrar warns antiguos sin ID si es necesario
    migrado = False
    for user_id, user_warns in warns.items():
        for warn in user_warns:
            if "id" not in warn:
                warn["id"] = obtener_proximo_id_warn(warns)
                migrado = True
    
    if migrado:
        guardar_warns(warns)
    
    if eliminar_warn_por_id(warns, warn_id):
        guardar_warns(warns)
        if lang == "en":
            embed = discord.Embed(
                title="✅ Warn deleted",
                color=discord.Color.green(),
                description=f"Warning #{warn_id} deleted successfully."
            )
        else:
            embed = discord.Embed(
                title="✅ Warn eliminado",
                color=discord.Color.green(),
                description=f"Warn #{warn_id} eliminado correctamente."
            )
        await ctx.send(embed=embed)
    else:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                color=discord.Color.red(),
                description=f"No warning found with ID #{warn_id}."
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                color=discord.Color.red(),
                description=f"No se encontró ningún warn con ID #{warn_id}."
            )
        await ctx.send(embed=embed)

# ---------- BAN COMMANDS ----------
@bot.hybrid_command(name="ban", description="Banea a un usuario del servidor (Solo staff) / Ban a user from the server (Staff only)")
async def ban(ctx, usuario: str, *, razón: str = "No especificada"):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Intentar obtener el usuario por mención o ID
    try:
        # Verificar si es una mención
        if usuario.startswith('<@') and usuario.endswith('>'):
            user_id = usuario.strip('<@!>')
            user = await bot.fetch_user(int(user_id))
        else:
            # Verificar si es un ID de usuario
            try:
                user = await bot.fetch_user(int(usuario))
            except ValueError:
                if lang == "en":
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Please provide a valid user mention or ID.",
                        color=discord.Color.red()
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Por favor proporciona una mención o ID de usuario válido.",
                        color=discord.Color.red()
                    )
                await ctx.send(embed=embed, ephemeral=True)
                return
    except discord.NotFound:
        if lang == "en":
            embed = discord.Embed(
                title="❌ User Not Found",
                description="User not found.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Usuario No Encontrado",
                description="Usuario no encontrado.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Verificar si el usuario está en el servidor
    member = ctx.guild.get_member(user.id)
    if member and es_staff(member):
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="You can't ban another staff member.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No puedes banear a otro miembro del staff.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    try:
        # Ban normal - solo la cuenta, sin eliminar mensajes por defecto
        await ctx.guild.ban(user, reason=razón, delete_message_days=0)
        
        if lang == "en":
            embed = discord.Embed(
                title="🔨 User banned",
                color=discord.Color.red(),
                description=f"{user.mention} has been banned from the server."
            )
            embed.add_field(name="Reason", value=razón, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Type", value="Account ban", inline=True)
            embed.set_footer(text="Only this specific account was banned")
        else:
            embed = discord.Embed(
                title="🔨 Usuario baneado",
                color=discord.Color.red(),
                description=f"{user.mention} ha sido baneado del servidor."
            )
            embed.add_field(name="Razón", value=razón, inline=False)
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="Tipo", value="Ban de cuenta", inline=True)
            embed.set_footer(text="Solo se baneó esta cuenta específica")
        
        await ctx.send(embed=embed)
    except discord.Forbidden:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="I don't have permissions to ban this user.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No tengo permisos para banear a este usuario.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
    except discord.HTTPException:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="Error banning the user.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Error al banear al usuario.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)

@bot.hybrid_command(name="banip", description="Banea a un usuario por IP (Solo staff) / Ban a user by IP (Staff only)")
async def banip(ctx, usuario: str, *, razón: str = "No especificada"):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Intentar obtener el usuario por mención o ID
    try:
        # Verificar si es una mención
        if usuario.startswith('<@') and usuario.endswith('>'):
            user_id = usuario.strip('<@!>')
            user = await bot.fetch_user(int(user_id))
        else:
            # Verificar si es un ID de usuario
            try:
                user = await bot.fetch_user(int(usuario))
            except ValueError:
                if lang == "en":
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Please provide a valid user mention or ID.",
                        color=discord.Color.red()
                    )
                else:
                    embed = discord.Embed(
                        title="❌ Error",
                        description="Por favor proporciona una mención o ID de usuario válido.",
                        color=discord.Color.red()
                    )
                await ctx.send(embed=embed, ephemeral=True)
                return
    except discord.NotFound:
        if lang == "en":
            embed = discord.Embed(
                title="❌ User Not Found",
                description="User not found.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Usuario No Encontrado",
                description="Usuario no encontrado.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Verificar si el usuario está en el servidor
    member = ctx.guild.get_member(user.id)
    if member and es_staff(member):
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="You can't ban another staff member.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No puedes banear a otro miembro del staff.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    try:
        # Ban por IP - elimina mensajes y previene evasión
        await ctx.guild.ban(user, reason=f"{razón} (IP ban)", delete_message_days=7)
        
        if lang == "en":
            embed = discord.Embed(
                title="🔨 User banned by IP",
                color=discord.Color.dark_red(),
                description=f"{user.mention} has been banned from the server by IP."
            )
            embed.add_field(name="Reason", value=razón, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
            embed.add_field(name="Messages deleted", value="7 days", inline=True)
            embed.add_field(name="Type", value="IP ban", inline=True)
            embed.set_footer(text="Prevents evasion with alternate accounts from the same IP")
        else:
            embed = discord.Embed(
                title="🔨 Usuario baneado por IP",
                color=discord.Color.dark_red(),
                description=f"{user.mention} ha sido baneado del servidor por IP."
            )
            embed.add_field(name="Razón", value=razón, inline=False)
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="Mensajes eliminados", value="7 días", inline=True)
            embed.add_field(name="Tipo", value="Ban por IP", inline=True)
            embed.set_footer(text="Previene evasión con cuentas alternativas de la misma IP")
        
        await ctx.send(embed=embed)
    except discord.Forbidden:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="I don't have permissions to ban this user.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No tengo permisos para banear a este usuario.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
    except discord.HTTPException:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="Error banning the user.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Error al banear al usuario.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)

@bot.hybrid_command(name="unban", description="Desbanea a un usuario (Solo staff) / Unban a user (Staff only)")
async def unban(ctx, user_id: str, *, razón: str = "No especificada"):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    try:
        user_id = int(user_id)
        user = await bot.fetch_user(user_id)
        
        await ctx.guild.unban(user, reason=razón)
        
        if lang == "en":
            embed = discord.Embed(
                title="✅ User unbanned",
                color=discord.Color.green(),
                description=f"{user.mention} has been unbanned from the server."
            )
            embed.add_field(name="User", value=f"{user.name}#{user.discriminator}", inline=True)
            embed.add_field(name="ID", value=user.id, inline=True)
            embed.add_field(name="Reason", value=razón, inline=False)
            embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        else:
            embed = discord.Embed(
                title="✅ Usuario desbaneado",
                color=discord.Color.green(),
                description=f"{user.mention} ha sido desbaneado del servidor."
            )
            embed.add_field(name="Usuario", value=f"{user.name}#{user.discriminator}", inline=True)
            embed.add_field(name="ID", value=user.id, inline=True)
            embed.add_field(name="Razón", value=razón, inline=False)
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)
    except ValueError:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="Invalid user ID.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="ID de usuario inválido.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
    except discord.NotFound:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="User not found or not banned.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Usuario no encontrado o no está baneado.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
    except discord.Forbidden:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="I don't have permissions to unban users.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No tengo permisos para desbanear usuarios.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
    except discord.HTTPException:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="Error unbanning the user.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Error al desbanear al usuario.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)

# ---------- CSV COMMAND ----------
@bot.hybrid_command(name="csv", description="Agrega datos al CSV / Add data to CSV")
async def csv_cmd(
    ctx,
    usuario: str,
    id_usuario: str,
    rol: str,
    dinero_devuelto: str,
    numero_devolucion: str,
    fecha: str
):
    lang = get_language(ctx.guild.id)
    
    if ctx.author.id not in CSV_ALLOWED_USERS:
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    if not all([usuario, id_usuario, rol, dinero_devuelto, numero_devolucion, fecha]):
        if lang == "en":
            embed = discord.Embed(
                title="❌ Incomplete Fields",
                description="All fields are required.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Campos Incompletos",
                description="Todos los campos son obligatorios.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    try:
        # Validar que id_usuario sea un número
        try:
            int(id_usuario)
        except ValueError:
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error",
                    description="User ID must be a number.",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="❌ Error",
                    description="El ID de usuario debe ser un número.",
                    color=discord.Color.red()
                )
            await ctx.send(embed=embed, ephemeral=True)
            return
        
        success, message = agregar_fila_csv(usuario, id_usuario, rol, dinero_devuelto, numero_devolucion, fecha)
        
        if success:
            if lang == "en":
                embed = discord.Embed(
                    title="✅ Data added to CSV",
                    color=0x00FF7F,
                    description=message
                )
                embed.add_field(name="User", value=usuario, inline=True)
                embed.add_field(name="ID", value=id_usuario, inline=True)
                embed.add_field(name="Role", value=rol, inline=True)
                embed.add_field(name="Money Returned", value=dinero_devuelto, inline=True)
                embed.add_field(name="Return Number", value=numero_devolucion, inline=True)
                embed.add_field(name="Date", value=fecha, inline=True)
            else:
                embed = discord.Embed(
                    title="✅ Datos agregados al CSV",
                    color=0x00FF7F,
                    description=message
                )
                embed.add_field(name="Usuario", value=usuario, inline=True)
                embed.add_field(name="ID", value=id_usuario, inline=True)
                embed.add_field(name="Rol", value=rol, inline=True)
                embed.add_field(name="Dinero Devuelto", value=dinero_devuelto, inline=True)
                embed.add_field(name="N° Devolución", value=numero_devolucion, inline=True)
                embed.add_field(name="Fecha", value=fecha, inline=True)
            
            await ctx.send(embed=embed)
        else:
            if lang == "en":
                embed = discord.Embed(
                    title="❌ Error adding data to CSV",
                    color=discord.Color.red(),
                    description=message
                )
            else:
                embed = discord.Embed(
                    title="❌ Error al agregar datos al CSV",
                    color=discord.Color.red(),
                    description=message
                )
            await ctx.send(embed=embed)
            
    except Exception as e:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error adding data: {e}",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error al agregar los datos: {e}",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)

@bot.hybrid_command(name="getcsv", description="Obtiene el archivo CSV / Get CSV file")
async def getcsv(ctx):
    lang = get_language(ctx.guild.id)
    
    if ctx.author.id not in CSV_ALLOWED_USERS:
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    csv_file = obtener_csv_como_archivo()
    if csv_file:
        # Eliminamos el embed y solo enviamos el archivo
        await ctx.send(file=csv_file)
    else:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="CSV file not found or is empty.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No se encontró el archivo CSV o está vacío.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)

@bot.hybrid_command(name="delcsv", description="Elimina fila del CSV / Delete CSV row")
async def delcsv(ctx, fila_id: int):
    lang = get_language(ctx.guild.id)
    
    if ctx.author.id not in CSV_ALLOWED_USERS:
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    success, message = eliminar_fila_csv_por_id(fila_id)
    
    if success:
        if lang == "en":
            embed = discord.Embed(
                title="✅ Row deleted from CSV",
                color=discord.Color.green(),
                description=message
            )
        else:
            embed = discord.Embed(
                title="✅ Fila eliminada del CSV",
                color=discord.Color.green(),
                description=message
            )
        await ctx.send(embed=embed)
    else:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error deleting row from CSV",
                color=discord.Color.red(),
                description=message
            )
        else:
            embed = discord.Embed(
                title="❌ Error al eliminar fila del CSV",
                color=discord.Color.red(),
                description=message
            )
        await ctx.send(embed=embed)

# ---------- RESET CSV COMMAND ----------
@bot.hybrid_command(name="resetcsv", description="Resetea el archivo CSV / Reset CSV file")
async def resetcsv(ctx):
    lang = get_language(ctx.guild.id)
    
    if ctx.author.id not in CSV_ALLOWED_USERS:
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    if lang == "en":
        embed = discord.Embed(
            title="⚠️ Reset CSV",
            description="Are you sure you want to reset the CSV file? This action cannot be undone.",
            color=discord.Color.orange()
        )
    else:
        embed = discord.Embed(
            title="⚠️ Reiniciar CSV",
            description="¿Estás seguro de que quieres reiniciar el archivo CSV? Esta acción no se puede deshacer.",
            color=discord.Color.orange()
        )
    
    view = ResetCSVView(ctx)
    await ctx.send(embed=embed, view=view)

# ---------- STAFF ----------
@bot.hybrid_command(name="mute", description="Mutea a un usuario (Solo staff) / Mute a user (Staff only)")
async def mute(ctx, member: discord.Member, tiempo: str = None, *, razón: str = "No especificada"):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permiso para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    if es_staff(member):
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="You can't mute another staff member.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No puedes mutear a otro miembro del staff.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Aislar al usuario en lugar de agregar rol "Muted"
    try:
        # Quitar todos los roles del usuario (excepto @everyone)
        roles_to_remove = [role for role in member.roles if role.name != "@everyone"]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)
        
        # Configurar permisos para cada canal para aislar al usuario
        for channel in ctx.guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                try:
                    await channel.set_permissions(member, view_channel=False, send_messages=False, connect=False, speak=False)
                except discord.Forbidden:
                    continue  # No tenemos permisos para este canal, continuar
        
        if lang == "en":
            embed = discord.Embed(
                title="🔇 User muted",
                color=discord.Color.orange(),
                description=f"{member.mention} has been muted and isolated."
            )
            embed.add_field(name="Reason", value=razón, inline=False)
        else:
            embed = discord.Embed(
                title="🔇 Usuario muteado",
                color=discord.Color.orange(),
                description=f"{member.mention} ha sido muteado y aislado."
            )
            embed.add_field(name="Razón", value=razón, inline=False)
    
        if tiempo:
            seconds = parse_time_to_seconds(tiempo)
            if seconds is None:
                if lang == "en":
                    embed_error = discord.Embed(
                        title="❌ Invalid Format",
                        description="Invalid time format. Examples: 5s, 10m, 1h, 1d, 1w",
                        color=discord.Color.red()
                    )
                else:
                    embed_error = discord.Embed(
                        title="❌ Formato Inválido",
                        description="Formato de tiempo inválido. Ejemplos: 5s, 10m, 1h, 1d, 1w",
                        color=discord.Color.red()
                    )
                await ctx.send(embed=embed_error, ephemeral=True)
                return
            
            if lang == "en":
                embed.add_field(name="Duration", value=tiempo, inline=True)
            else:
                embed.add_field(name="Duración", value=tiempo, inline=True)
            await ctx.send(embed=embed)
            
            # Programar el desmuteo automático
            await asyncio.sleep(seconds)
            
            # Restaurar permisos del usuario
            for channel in ctx.guild.channels:
                if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                    try:
                        await channel.set_permissions(member, overwrite=None)
                    except discord.Forbidden:
                        continue
            
            if lang == "en":
                embed_unmute = discord.Embed(
                    title="🔊 User unmuted",
                    color=discord.Color.green(),
                    description=f"{member.mention} has been automatically unmuted and permissions restored."
                )
            else:
                embed_unmute = discord.Embed(
                    title="🔊 Usuario desmuteado",
                    color=discord.Color.green(),
                    description=f"{member.mention} ha sido desmuteado automáticamente y se restauraron sus permisos."
                )
            await ctx.channel.send(embed=embed_unmute)
        else:
            if lang == "en":
                embed.add_field(name="Duration", value="Indefinite", inline=True)
            else:
                embed.add_field(name="Duración", value="Indefinido", inline=True)
            await ctx.send(embed=embed)
            
    except discord.Forbidden:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                description="I don't have permissions to mute this user.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="No tengo permisos para mutear a este usuario.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)

@bot.hybrid_command(name="unmute", description="Desmutea a un usuario (Solo staff) / Unmute a user (Staff only)")
async def unmute(ctx, member: discord.Member):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    try:
        # Restaurar todos los permisos del usuario en todos los canales
        for channel in ctx.guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                try:
                    await channel.set_permissions(member, overwrite=None)
                except discord.Forbidden:
                    continue  # No tenemos permisos para este canal, continuar
        
        if lang == "en":
            embed = discord.Embed(
                title="🔊 User unmuted",
                color=discord.Color.green(),
                description=f"{member.mention} has been unmuted and permissions restored."
            )
        else:
            embed = discord.Embed(
                title="🔊 Usuario desmuteado",
                color=discord.Color.green(),
                description=f"{member.mention} ha sido desmuteado y se restauraron sus permisos."
            )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                color=discord.Color.red(),
                description="I don't have permissions to unmute this user."
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                color=discord.Color.red(),
                description="No tengo permisos para desmutear a este usuario."
            )
        await ctx.send(embed=embed, ephemeral=True)

@bot.hybrid_command(name="lock", description="Bloquea un canal (Solo staff) / Lock a channel (Staff only)")
async def lock(ctx, canal: discord.TextChannel = None):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    canal = canal or ctx.channel
    overwrite = canal.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = False
    await canal.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    
    if lang == "en":
        embed = discord.Embed(
            title="🔒 Channel locked",
            color=discord.Color.orange(),
            description=f"{canal.mention} has been locked."
        )
    else:
        embed = discord.Embed(
            title="🔒 Canal bloqueado",
            color=discord.Color.orange(),
            description=f"{canal.mention} ha sido bloqueado."
        )
    await ctx.send(embed=embed)

@bot.hybrid_command(name="unlock", description="Desbloquea un canal (Solo staff) / Unlock a channel (Staff only)")
async def unlock(ctx, canal: discord.TextChannel = None):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    canal = canal or ctx.channel
    overwrite = canal.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = None
    await canal.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    
    if lang == "en":
        embed = discord.Embed(
            title="🔓 Channel unlocked",
            color=discord.Color.green(),
            description=f"{canal.mention} has been unlocked."
        )
    else:
        embed = discord.Embed(
            title="🔓 Canal desbloqueado",
            color=discord.Color.green(),
            description=f"{canal.mention} ha sido desbloqueado."
        )
    await ctx.send(embed=embed)

@bot.hybrid_command(name="clear", description="Elimina mensajes (1-500) (Solo staff) / Delete messages (1-500) (Staff only)")
async def clear(ctx, cantidad: int):
    lang = get_language(ctx.guild.id)
    
    if not tiene_permiso_staff(ctx):
        if lang == "en":
            embed = discord.Embed(
                title="❌ No Permissions",
                description="You don't have permission to use this command.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Sin Permisos",
                description="No tienes permisos para usar este comando.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    if cantidad < 1 or cantidad > 500:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Invalid Amount",
                description="The amount must be between 1 and 500 messages.",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="❌ Cantidad Inválida",
                description="La cantidad debe estar entre 1 and 500 mensajes.",
                color=discord.Color.red()
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    # Eliminar el comando primero
    await ctx.message.delete()
    
    # Luego eliminar los mensajes solicitados
    deleted = await ctx.channel.purge(limit=cantidad)
    
    if lang == "en":
        embed = discord.Embed(
            title="🧹 Messages deleted",
            color=discord.Color.orange(),
            description=f"{len(deleted)} messages have been deleted."
        )
    else:
        embed = discord.Embed(
            title="🧹 Mensajes eliminados",
            color=discord.Color.orange(),
            description=f"Se eliminaron {len(deleted)} mensajes."
        )
    msg = await ctx.send(embed=embed)

# ---------- INFO ----------
@bot.hybrid_command(name="avatar", aliases=["av"], description="Muestra el avatar de un usuario / Shows a user's avatar")
async def avatar(ctx, member: discord.Member = None):
    lang = get_language(ctx.guild.id)
    
    member = member or ctx.author
    
    if lang == "en":
        embed = discord.Embed(
            title=f"🖼️ Avatar of {member.display_name}",
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title=f"🖼️ Avatar de {member.display_name}",
            color=discord.Color.blue()
        )
    
    # Usar la imagen grande como imagen principal del embed
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    embed.set_image(url=avatar_url)
    
    # Eliminamos el thumbnail para que solo quede la imagen grande
    if lang == "en":
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    else:
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name="userinfo", description="Muestra información de un usuario / Shows user information")
async def userinfo(ctx, member: discord.Member = None):
    lang = get_language(ctx.guild.id)
    
    member = member or ctx.author
    
    if lang == "en":
        embed = discord.Embed(
            title=f"👤 Information of {member.display_name}",
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title=f"👤 Información de {member.display_name}",
            color=discord.Color.blue()
        )
    
    # Avatar como thumbnail
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)
    elif member.default_avatar:
        embed.set_thumbnail(url=member.default_avatar.url)
    
    if lang == "en":
        embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="👤 Name", value=f"`{str(member)}`", inline=True)
        embed.add_field(name="📅 Account created", value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
        embed.add_field(name="📥 Joined server", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
    else:
        embed.add_field(name="🆔 ID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="👤 Nombre", value=f"`{str(member)}`", inline=True)
        embed.add_field(name="📅 Cuenta creada", value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
        embed.add_field(name="📥 Se unió al servidor", value=member.joined_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
    
    roles = [r.mention for r in member.roles if r.name != "@everyone"]
    if lang == "en":
        embed.add_field(name="🎭 Roles", value=", ".join(roles) if roles else "None", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    else:
        embed.add_field(name="🎭 Roles", value=", ".join(roles) if roles else "Ninguno", inline=False)
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name="serverinfo", description="Muestra información del servidor / Shows server information")
async def serverinfo(ctx):
    lang = get_language(ctx.guild.id)
    
    guild = ctx.guild
    
    if lang == "en":
        embed = discord.Embed(
            title=f"📊 Server information {guild.name}",
            color=discord.Color.blue()
        )
    else:
        embed = discord.Embed(
            title=f"📊 Información del servidor {guild.name}",
            color=discord.Color.blue()
        )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    if lang == "en":
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created", value=guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Verification level", value=str(guild.verification_level).title(), inline=True)
        embed.add_field(name="Boost", value=f"Level {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=True)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    else:
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Propietario", value=guild.owner.mention if guild.owner else "Desconocido", inline=True)
        embed.add_field(name="Creado", value=guild.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=False)
        embed.add_field(name="Miembros", value=guild.member_count, inline=True)
        embed.add_field(name="Canales", value=len(guild.channels), inline=True)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Nivel de verificación", value=str(guild.verification_level).title(), inline=True)
        embed.add_field(name="Boost", value=f"Nivel {guild.premium_tier} ({guild.premium_subscription_count} boosts)", inline=True)
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    
    await ctx.send(embed=embed)

@bot.hybrid_command(name="servericon", description="Muestra el icono del servidor / Shows the server icon")
async def servericon(ctx):
    lang = get_language(ctx.guild.id)
    
    if not ctx.guild.icon:
        if lang == "en":
            embed = discord.Embed(
                title="❌ Error",
                color=discord.Color.red(),
                description="This server has no icon."
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                color=discord.Color.red(),
                description="Este servidor no tiene icono."
            )
        await ctx.send(embed=embed, ephemeral=True)
        return
    
    if lang == "en":
        embed = discord.Embed(  # Corregido: Embrid -> Embed
            title=f"🖼️ Server icon {ctx.guild.name}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    else:
        embed = discord.Embed(
            title=f"🖼️ Icono del servidor {ctx.guild.name}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
    
    embed.set_image(url=ctx.guild.icon.url)
    
    await ctx.send(embed=embed)

# ---------- HELP ----------
@bot.hybrid_command(name="help", description="Muestra el menú de ayuda / Shows the help menu")
async def help(ctx):
    lang = get_language(ctx.guild.id)
    
    if lang == "en":
        embed = discord.Embed(
            title="📖 Help Menu - Clapex",
            description="You can use commands with `?` or `/`",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title="📖 Menu de Ayuda - Clapex",
            description="Puedes usar los comandos con `?` o `/`",
            color=discord.Color.green()
        )
    
    # Comandos de staff
    if tiene_permiso_staff(ctx):
        if lang == "en":
            embed.add_field(
                name="🛠️ Staff Commands", 
                value="`prefix`, `announce`, `autorole`, `mute`, `unmute`, `lock`, `unlock`, `clear`, `warn`, `warnings`, `allwarnings`, `delwarn`, `addpoints`, `removepoints`, `pregunta`, `ban`, `banip`, `unban`", 
                inline=False
            )
        else:
            embed.add_field(
                name="🛠️ Comandos de Staff", 
                value="`prefix`, `announce`, `autorole`, `mute`, `unmute`, `lock`, `unlock`, `clear`, `warn`, `warnings`, `allwarnings`, `delwarn`, `addpoints`, `removepoints`, `pregunta`, `ban`, `banip`, `unban`", 
                inline=False
            )
    
    # Comandos de administrador
    if es_admin(ctx.author):
        if lang == "en":
            embed.add_field(
                name="👑 Admin Commands", 
                value="`language` - Change bot language", 
                inline=False
            )
        else:
            embed.add_field(
                name="👑 Comandos de Administrador", 
                value="`language` - Cambiar idioma del bot", 
                inline=False
            )
    
    # Comandos públicos
    if lang == "en":
        embed.add_field(
            name="🏆 Ranking Commands", 
            value="`rank`, `ranking`", 
            inline=False
        )
        embed.add_field(
            name="🎮 Trivia Commands", 
            value="`trivia`", 
            inline=False
        )
        embed.add_field(
            name="ℹ️ Information Commands", 
            value="`avatar` (`av`), `userinfo`, `serverinfo`, `servericon`", 
            inline=False
        )
    else:
        embed.add_field(
            name="🏆 Comandos de Ranking", 
            value="`rank`, `ranking`", 
            inline=False
        )
        embed.add_field(
            name="🎮 Comandos de Trivia", 
            value="`trivia`", 
            inline=False
        )
        embed.add_field(
            name="ℹ️ Comandos de Información", 
            value="`avatar` (`av`), `userinfo`, `serverinfo`, `servericon`", 
            inline=False
        )
    
    # Comando csv solo para usuarios autorizados
    if ctx.author.id in CSV_ALLOWED_USERS:
        if lang == "en":
            embed.add_field(
                name="📊 CSV Commands (Private)", 
                value="`csv`, `getcsv`, `delcsv`, `resetcsv` - Manage returns data", 
                inline=False
            )
        else:
            embed.add_field(
                name="📊 Comandos CSV (Privado)", 
                value="`csv`, `getcsv`, `delcsv`, `resetcsv` - Gestionar datos de devoluciones", 
                inline=False
            )

    if lang == "en":
        embed.set_footer(text="Use ?help or /help to see this message")
    else:
        embed.set_footer(text="Usa ?help o /help para ver este mensaje")

    await ctx.send(embed=embed)

# ---------- MANTENER BOT 24/7 ----------
app = Flask('')
@app.route('/')
def home():
    return "Bot activo"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Ejecutar el bot
if __name__ == "__main__":
    keep_alive()
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(f"❌ Error al conectar el bot: {e}")