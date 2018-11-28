from cg.store import models


class BaseHandler:
    User = models.User
    Customer = models.Customer
    CustomerGroup = models.CustomerGroup
    Sample = models.Sample
    Family = models.Family
    FamilySample = models.FamilySample
    Flowcell = models.Flowcell
    Analysis = models.Analysis
    Application = models.Application
    ApplicationVersion = models.ApplicationVersion
    Panel = models.Panel
    Pool = models.Pool
    Delivery = models.Delivery
    Invoice = models.Invoice
    MicrobialSample = models.MicrobialSample
    MicrobialOrder = models.MicrobialOrder
    Organism = models.Organism
