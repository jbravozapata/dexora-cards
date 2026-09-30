# Dexora Cards Mobile

Cliente Flutter para Android e iOS. Comparte usuarios, catálogo, colección TCG, wishlist, perfil y progreso de **Mis 1025 Pokémon** con el backend Django.

```powershell
flutter pub get
flutter analyze
flutter test
flutter run --dart-define=DEXORA_API_URL=http://10.0.2.2:8002/api/v1
```

`10.0.2.2` es la dirección del equipo anfitrión desde el emulador Android. La pantalla de acceso permite cambiarla: para un teléfono físico usa la IP LAN del servidor y mantén ambos dispositivos en la misma red. Nunca incluyas tokens o direcciones de producción directamente en el código.
