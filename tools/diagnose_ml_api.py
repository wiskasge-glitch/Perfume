import asyncio

from app.clients.mercadolibre import (
    MercadoLibreAPIError,
    MercadoLibreClient,
)


ITEM_ID = "MLM2638718467"


async def main() -> None:
    async with MercadoLibreClient() as client:

        print("\n1. Probando autenticación con /users/me")

        try:
            user = await client.get_current_user()

            print("✅ Token válido")
            print(f"Usuario ID: {user.get('id')}")
            print(f"Nickname: {user.get('nickname')}")

        except MercadoLibreAPIError as error:
            print(f"❌ Error de autenticación: {error}")
            return

        print(f"\n2. Probando publicación {ITEM_ID}")

        try:
            item = await client.get_item(ITEM_ID)

            print("✅ Publicación accesible")
            print(f"Título: {item.get('title')}")
            print(f"Seller ID: {item.get('seller_id')}")

        except MercadoLibreAPIError as error:
            print(f"❌ Publicación rechazada: {error}")


if __name__ == "__main__":
    asyncio.run(main())