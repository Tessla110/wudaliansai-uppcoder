FROM alpine:3.20
COPY --from=iptvtop/wudaliansai /wudaliansai /wudaliansai
COPY --from=iptvtop/wudaliansai /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
CMD sh -c 'BIND=0.0.0.0:${PORT:-18765} exec /wudaliansai'
