import asyncio
from objects import glob
from objects.db import PostgresDB
from utils import pp
from objects.player import recalc_stats

glob.db = PostgresDB()

async def recalc():
    await glob.db.connect()
    # await insert_whitelist()
    await pp.recalc_scores() 
    # await pp.recalc_single_score(13061)   
    await recalc_stats()
    
    



async def main():
    await recalc()
   

if __name__ == "__main__":
    asyncio.run(main())