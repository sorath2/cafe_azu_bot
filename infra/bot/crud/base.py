# from sqlalchemy.future import select
# from sqlalchemy.orm import selectinload
#
# from core.db import AsyncSession
#
# from models import Cafe
#
#
# class CRUDBase:
#     def __init__(self, session: AsyncSession):
#         self._session = session
#
#     async def get_cafes_info(self):
#         res = await self._session.execute(
#             select(Cafe).options(selectinload(Cafe.tables))
#         )
#
#         return res.scalars().all()
