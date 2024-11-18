# Eco and Animal Liberation Story Map

```bash
docker build -t ocr-app .
docker voolume create appvol
docker run -itd --rm --name eco-ar ocr-app --volume appvol:/app
docker exec -it eco-ar /bin/bash
docker stop eco-ar
docker stop eco-ar
```
