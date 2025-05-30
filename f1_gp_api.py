from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse, StreamingResponse
import fastf1
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from io import StringIO
import pandas as pd

app = FastAPI(title="F1 Grand Prix API", version="1.0")


async def rich_stream(year: int, round: int, session: str):
    buffer = StringIO()
    console = Console(file= buffer, force_terminal=True, width=80)
    text = "GRAND PRIX API 🏁🏎️"
    console.print(Panel(text))
    yield buffer.getvalue()

    buffer.truncate(0)
    buffer.seek(0)

    console.print("\n Espera un segundo... ⌛\n")
    yield buffer.getvalue()
    buffer.truncate(0)
    buffer.seek(0)

    try:
        session_ = fastf1.get_session(year, round, session)
        session_.load()
        
        console.print(f" GP: {session_.event['EventName']}")
        console.print(f"📍 Location: {session_.event['Location']}")
        winner = session_.results.iloc[0]
        console.print(f"🏆 {'Winner' if session == 'r' else 'Fastest'}: [bold green]{winner.FullName} {winner.DriverNumber}[/bold green]")
        console.print(f"🚩 Team: [cyan]{winner.TeamName}[/cyan]")
        console.print(f"⏰ Time {'Q3' if session =='q' else ''}: [yellow]{format_timedelta(winner.Q3) if session == 'q' else format_timedelta(winner.Time)}[/yellow]\n")


        table = Table(title="Grand Prix Results")
        table.add_column("Pos", justify="right", style="bold blue")
        table.add_column("Pilot", style="bold")
        table.add_column("Team", style="green")
        if session == 'q':
            table.add_column("Q1", justify="right", style="yellow")
            table.add_column("Q2", justify="right", style="yellow")
            table.add_column("Q3", justify="right", style="yellow") 
            
            for i, row in session_.results.iterrows():
                table.add_row(
                str(int(row.Position)),
                row.FullName,
                row.TeamName,
                format_timedelta(row.Q1),
                format_timedelta(row.Q2),
                format_timedelta(row.Q3)
                # str(row.Q1) if not pd.isna(row.Q1) else "-",
                # str(row.Q2) if not pd.isna(row.Q2) else "-",
                # str(row.Q3) if not pd.isna(row.Q3) else "-"
            )

        else:
            table.add_column("Time", justify="right", style="yellow")

            for i, row in session_.results.iterrows():
                table.add_row(
                str(int(row.Position)),
                row.FullName,
                row.TeamName,
                str(row.Time)
            )
        
        
        console.print(table)

        # console.print(session_.results.drop(columns=['Abbreviation', 'DriverId', 'TeamColor', 'TeamId', 
        #                                              'FirstName', 'LastName', 'FullName','HeadshotUrl', 
        #                                              'CountryCode', 'Status']))

        yield buffer.getvalue()
        buffer.truncate(0)
        buffer.seek(0)

    except Exception as e:
        console.print(f"[bold red]❌ Error al cargar el gran premio:[/bold red] {str(e)}")
        yield buffer.getvalue()
        buffer.truncate(0)
        buffer.seek(0)

    


@app.get("/grand_prix/{year}/{round}/{session}")
async def grand_prix(year: int, round: int, session: str):
    stream = rich_stream(year, round, session)
    return StreamingResponse(stream, media_type="text/plain")


def format_timedelta(td: pd.Timedelta) -> str:
    if pd.isna(td):
        return "-"
    
    total_seconds = td.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:06.3f}" 