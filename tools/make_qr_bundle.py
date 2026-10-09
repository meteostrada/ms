#!/usr/bin/env python3
"""Crea un unico file JS con il generatore di QR (QRCode for JavaScript, Kazuhiko Arase, licenza MIT),
pronto da incollare nel sito. Uso: make_qr_bundle.py <cartella vendor/QRCode> > qr.js
La cartella e' quella che si trova dentro il pacchetto npm "qrcode-terminal".
"""
import os, sys, re
src = sys.argv[1]
order = ["QRMode", "QRErrorCorrectLevel", "QRMaskPattern", "QRMath", "QRPolynomial", "QRUtil",
         "QRRSBlock", "QRBitBuffer", "QR8bitByte", "index"]
out = ["/* QRCode for JavaScript - Copyright (c) 2009 Kazuhiko Arase - MIT license (http://www.opensource.org/licenses/mit-license.php).",
       "   The word \"QR Code\" is a registered trademark of DENSO WAVE INCORPORATED. */",
       "var msQRLib = (function () {", "var mods = {}, defs = {};"]
for name in order:
    code = open(os.path.join(src, name + ".js"), encoding="utf-8").read()
    # tolgo i commenti di intestazione lunghi (restano nel commento sopra)
    code = re.sub(r"^//-+\n(?://.*\n)+//-+\n", "", code, flags=re.M)
    key = "./" + name
    out.append("defs[%s] = function (module, require) {\n%s\n};" % (repr(key).replace("'", '"'), code))
out.append("""function req(k) {
  if (!mods[k]) { var m = { exports: {} }; mods[k] = m; defs[k](m, req); }
  return mods[k].exports;
}
return req("./index");
})();
/* Restituisce { size, dark(r, c) } per un testo (solo caratteri ASCII). ecc: 1 = L, 0 = M, 3 = Q, 2 = H (come la libreria). */
function msQR(text, ecc) {
  var q = new msQRLib(0, ecc == null ? 0 : ecc);
  q.addData(text); q.make();
  return { size: q.getModuleCount(), dark: function (r, c) { return q.isDark(r, c); } };
}""")
print("\n".join(out))
